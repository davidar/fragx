#include <GLES3/gl3.h>
#include <SDL2/SDL.h>

GLuint LoadShader(const char *shaderSrc, GLenum type) {
  GLuint shader = glCreateShader(type);
  if (shader == 0) return 0;
  glShaderSource(shader, 1, &shaderSrc, NULL);
  glCompileShader(shader);
  GLint compiled; glGetShaderiv(shader, GL_COMPILE_STATUS, &compiled);
  if (!compiled) {
    SDL_Log("Error compiling shader");
    GLint infoLen = 0; glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &infoLen);
    if (infoLen > 1) {
      char *infoLog = malloc(sizeof(char) * infoLen);
      glGetShaderInfoLog(shader, infoLen, NULL, infoLog);
      SDL_Log("%s", infoLog);
      free(infoLog);
    }
    glDeleteShader(shader);
    return 0;
  }
  return shader;
}

GLuint LoadProgram(const char *fragSrc) {
  const char *vertSrc = "attribute vec4 p;void main(){gl_Position=p;}";
  GLuint vert = LoadShader(vertSrc, GL_VERTEX_SHADER);
  GLuint frag = LoadShader(fragSrc, GL_FRAGMENT_SHADER);
  GLuint program = glCreateProgram();
  glAttachShader(program, vert);
  glAttachShader(program, frag);
  glBindAttribLocation(program, 0, "p");
  glLinkProgram(program);
  GLint linked; glGetProgramiv(program, GL_LINK_STATUS, &linked);
  if (!linked) {
    SDL_Log("Error linking program");
    GLint infoLen = 0; glGetProgramiv(program, GL_INFO_LOG_LENGTH, &infoLen);
    if (infoLen > 1) {
      char *infoLog = malloc(sizeof(char) * infoLen);
      glGetProgramInfoLog(program, infoLen, NULL, infoLog);
      SDL_Log("%s", infoLog);
      free(infoLog);
    }
    glDeleteProgram(program);
    return 0;
  }
  glDeleteShader(vert);
  glDeleteShader(frag);
  return program;
}

GLuint Texture(GLsizei width, GLsizei height, GLint wrap) {
  GLuint texture; glGenTextures(1, &texture);
  glBindTexture(GL_TEXTURE_2D, texture);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, NULL);
  glBindTexture(GL_TEXTURE_2D, 0);
  return texture;
}

GLuint Framebuffer(GLuint texture) {
  GLuint framebuffer; glGenFramebuffers(1, &framebuffer);
  glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
  glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0);
  if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
    SDL_Log("Error creating framebuffer");
    return 0;
  }
  return framebuffer;
}

void UniformTexture(GLint location, GLint i, GLuint texture) {
  glActiveTexture(GL_TEXTURE0 + i);
  glBindTexture(GL_TEXTURE_2D, texture);
  glUniform1i(location, i);
}

static const GLfloat quad_vertices[] = {
  -1, -1, 0,
  +1, -1, 0,
  +1, +1, 0,
  +1, +1, 0,
  -1, +1, 0,
  -1, -1, 0,
};

SDL_Window *Init(int width, int height) {
  if (SDL_Init(SDL_INIT_VIDEO) != 0) {
    SDL_Log("Unable to initialize SDL: %s", SDL_GetError());
    return NULL;
  }

  SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);

  SDL_Window *window = SDL_CreateWindow(__FILE__, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL);
  if (window == NULL) {
    SDL_Log("Could not create window: %s", SDL_GetError());
    return NULL;
  } 

  SDL_GLContext glcontext = SDL_GL_CreateContext(window);

  SDL_GL_SetSwapInterval(1); // vsync

  SDL_Log("GL_RENDERER: %s", glGetString(GL_RENDERER));
  SDL_Log("GL_VERSION: %s", glGetString(GL_VERSION));
  SDL_Log("GL_SHADING_LANGUAGE_VERSION: %s", glGetString(GL_SHADING_LANGUAGE_VERSION));

  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, quad_vertices);
  glEnableVertexAttribArray(0);

  return window;
}
