#!/usr/bin/env python3
import os.path
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.realpath(__file__))

prelude = '''
int main(void) {
  int width = 800, height = 600;
  SDL_Window *window = Init(width, height);
'''

xbuf_init = '''
  GLuint program{k} = LoadProgram(xbuf{k}_frag);
  GLuint texture{k}[2];
  texture{k}[0] = Texture(width, height, {wrap}, GL_FLOAT, NULL);
  texture{k}[1] = Texture(width, height, {wrap}, GL_FLOAT, NULL);
  GLuint framebuffer{k}[2];
  framebuffer{k}[0] = Framebuffer(texture{k}[0]);
  framebuffer{k}[1] = Framebuffer(texture{k}[1]);
'''

run_program = '''
    glUseProgram(program{k});
    glUniform3f(glGetUniformLocation(program{k}, "iResolution"), width, height, 1);
    glUniform1f(glGetUniformLocation(program{k}, "iTimeDelta"), time_delta);
    glUniform1f(glGetUniformLocation(program{k}, "iTime"), time);
    glUniform1i(glGetUniformLocation(program{k}, "iFrame"), i);
'''

eventloop = '''
    SDL_GL_SwapWindow(window);
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
      switch (event.type) {
        case SDL_QUIT:
          SDL_DestroyWindow(window);
          SDL_Quit();
          exit(0);
      }
    }
'''

xbuf_src = {}
xbuf_wrap = {}
xbuf_map = {}
xbuf_keys = []

textures = []
tex_map = {}

def include(fname):
    src = []
    with open(fname, 'r') as f:
        for line in f:
            if line.startswith('#include'):
                src += include(os.path.join(os.path.dirname(fname), line.split()[1][1:-1]))
            else:
                src.append(line)
    src.append('\n')
    return src

def parse(fname):
    xbuf_map[fname] = {}
    tex_map[fname] = {}
    src = include(fname)
    for line in src:
        if '//!' in line:
            decl, ctrl = line.split('//!')
            uniform = decl.strip()[:-1].split()[-1]
            ctyp, args = ctrl.strip()[:-1].split('[')
            params = {}
            for i, arg in enumerate(args.split(',')):
                if ':' in arg:
                    key, val = arg.split(':')
                    params[key.strip()] = val.strip()
                else:
                    params[i] = arg.strip()
            if ctyp == 'buffer':
                xbuf = os.path.join(os.path.dirname(fname), params['xbuf'])
                if xbuf not in xbuf_src:
                    xbuf_src[xbuf] = None # prevent infinite recursion
                    xbuf_src[xbuf] = parse(xbuf)
                if 'wrap' in params: xbuf_wrap[xbuf] = params['wrap']
                xbuf_map[fname][uniform] = xbuf
            elif ctyp == 'texture':
                texture = params[0].replace('"', '')
                if texture not in textures: textures.append(texture)
                tex_map[fname][uniform] = textures.index(texture)
    return ''.join(src)

def shader(fname, src):
    src = '#version 300 es\n' + src
    with open(fname, 'w') as f:
        f.write(src)
    try:
        subprocess.run([os.path.join(DIR, 'bin', 'glslangValidator'), fname], stdout=sys.stderr, check=True)
    except subprocess.CalledProcessError:
        for no, line in enumerate(src.split('\n'), 1):
            sys.stderr.write('{:>4} {}\n'.format(no, line))
    subprocess.run(['mono', os.path.join(DIR, 'bin', 'shader_minifier.exe'), '--no-renaming', fname, '-o', fname + '.h'])
    with open(fname + '.h', 'r') as f:
        return f.read()

def render(fname, k=''):
    print(run_program.format(k=k))
    for u, uniform in enumerate(tex_map[fname]):
        print('    UniformTexture(glGetUniformLocation(program{}, "{}"), {}, image{});'.format(k, uniform, u, tex_map[fname][uniform]))
    for u, uniform in enumerate(xbuf_map[fname], len(tex_map[fname])):
        j = xbuf_keys.index(xbuf_map[fname][uniform])
        i = 'i' if k == '' or k > j else '(i+1)'
        print('    UniformTexture(glGetUniformLocation(program{}, "{}"), {}, texture{}[{}%2]);'.format(k, uniform, u, j, i))
    print('    glDrawArrays(GL_TRIANGLES, 0, 6);')

def main():
    src = parse(sys.argv[1])
    xbuf_keys.extend(xbuf_src.keys())
    xbuf_keys.sort()
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(os.path.join(DIR, 'fragx.h'), 'r') as f: print(f.read())
        for i, fname in enumerate(textures):
            if not os.path.isfile(fname):
                fname = os.path.join(DIR, 'synthclipse', 'org.synthclipse.include', 'include', fname)
            with open(fname, 'rb') as f:
                data = ','.join(str(b) for b in f.read())
            print('static unsigned char image{}_data[] = {{{}}};'.format(i, data))
        print(shader(os.path.join(tmpdirname, 'main.frag'), src))
        for k, fname in enumerate(xbuf_keys):
            print(shader(os.path.join(tmpdirname, 'xbuf{}.frag'.format(k)), xbuf_src[fname]))

        print(prelude)
        for i, fname in enumerate(textures):
            print('  GLuint image{i} = TextureImage(image{i}_data, sizeof(image{i}_data), GL_REPEAT);'.format(i=i))
        print('  GLuint program = LoadProgram(main_frag);')
        for k, fname in enumerate(xbuf_keys):
            print(xbuf_init.format(k=k, wrap=xbuf_wrap.get(fname, 'GL_REPEAT')))

        print('  GLfloat time = 0;')
        print('  for (int i = 0;; i++) {')
        print('    GLfloat time_delta = 1e-3 * SDL_GetTicks() - time;')
        print('    time += time_delta;')
        for k, fname in enumerate(xbuf_keys):
            print('    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer{k}[i%2]);'.format(k=k))
            render(fname, k)
        print('    glBindFramebuffer(GL_FRAMEBUFFER, 0);')
        render(sys.argv[1])
        print(eventloop)
        print('  }')
        print('}')
if __name__ == '__main__': main()
