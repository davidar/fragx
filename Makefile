LDLIBS = -lGL -lSDL2

bin/shader_minifier.exe:
	wget https://github.com/laurentlb/Shader_Minifier/releases/download/1.1.6/shader_minifier.exe -O $@

bin/glslangValidator: glslang/build/install/bin/glslangValidator
	cp "$<" "$@"

glslang/build/install/bin/glslangValidator:
	./build-glslang.sh

bin/%.c: glsl/src/%.fragx bin/shader_minifier.exe bin/glslangValidator
	./fragx.py "$<" > "$@"
