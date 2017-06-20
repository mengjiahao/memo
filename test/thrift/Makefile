THRIFT_VER =thrift-0.10.0
USR_DIR    =/usr/local
INCS_DIRS  =-I${USR_DIR}/include
LIBS_DIRS  =-L${USR_DIR}/lib
CPP_DEFS   =
CPP_OPTS   =-Wall -O2
LIBS       =-lthrift

GEN_SRC    = ./gen-cpp/SharedService.cpp  \
             ./gen-cpp/shared_types.cpp   \
             ./gen-cpp/tutorial_types.cpp \
             ./gen-cpp/Calculator.cpp
GEN_INC    = -I./gen-cpp

MY_SRC     = ./src

default: server client

gen:
	thrift -r --gen cpp ${MY_SRC}/shared.thrift
	thrift -r --gen cpp ${MY_SRC}/tutorial.thrift

server: ${MY_SRC}/CppServer.cpp
	g++ ${CPP_OPTS} ${CPP_DEFS} -o CppServer ${GEN_INC} ${INCS_DIRS} ${MY_SRC}/CppServer.cpp ${GEN_SRC} ${LIBS_DIRS} ${LIBS}

client: ${MY_SRC}/CppClient.cpp
	g++ ${CPP_OPTS} ${CPP_DEFS} -o CppClient ${GEN_INC} ${INCS_DIRS} ${MY_SRC}/CppClient.cpp ${GEN_SRC} ${LIBS_DIRS} ${LIBS}

clean:
	$(RM) -rf ./gen-cpp CppClient CppServer