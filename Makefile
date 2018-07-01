LDLIBS = -lGL -lSDL2

bin/shader_minifier.exe:
	wget https://github.com/laurentlb/Shader_Minifier/releases/download/1.1.6/shader_minifier.exe -O $@

bin/%.c: glsl/src/%.fragx bin/shader_minifier.exe
	./fragx.py "$<" > "$@"
