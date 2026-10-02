CXX ?= g++
CPPFLAGS := -Isrc
WARNINGS := -Wall -Wextra -Wpedantic -Wconversion -Wshadow
CXXFLAGS ?= -std=c++17 $(WARNINGS)
OPENMP ?= 1
ifeq ($(OPENMP),1)
OPENMP_FLAGS := -fopenmp
BUILD_DIR ?= build
else
OPENMP_FLAGS :=
BUILD_DIR ?= build/serial-only
endif
DEBUG_DIR := $(BUILD_DIR)/debug
BENCHMARK_DIR := $(BUILD_DIR)/benchmark
PROFILE_DIR := $(BUILD_DIR)/profile
DEBUG_TARGET := $(DEBUG_DIR)/life
TEST_TARGET := $(DEBUG_DIR)/life_tests
BENCHMARK_TARGET := $(BENCHMARK_DIR)/life
PROFILE_TARGET := $(PROFILE_DIR)/life
NVCC ?= nvcc
# Verified by allocated-device query 623393: A100 compute capability 8.0.
CUDA_ARCH ?= 80
CUDA_FLAGS ?= -std=c++17 -O3 -lineinfo -arch=sm_$(CUDA_ARCH)
CUDA_DIR := $(BUILD_DIR)/cuda
CUDA_LINK_FLAGS := $(if $(OPENMP_FLAGS),-Xcompiler=$(OPENMP_FLAGS))

# Avoid loading an incompatible libstdc++ DLL when several MinGW installations
# appear on a Windows PATH. Rangpur/Linux keeps its normal dynamic toolchain.
ifeq ($(OS),Windows_NT)
LDFLAGS += -static
endif

.PHONY: all debug benchmark profile test clean
.PHONY: cuda cuda-test

cuda: $(CUDA_DIR)/life $(CUDA_DIR)/life_cuda_tests

cuda-test: cuda
	$(CUDA_DIR)/life_cuda_tests

$(CUDA_DIR)/life.o: src/life.cpp src/life.h Makefile | $(CUDA_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O3 -DNDEBUG -c $< -o $@

$(CUDA_DIR)/main.o: src/main.cpp src/life.h src/life_cuda.h Makefile | $(CUDA_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O3 -DNDEBUG -DLIFE_ENABLE_CUDA -c $< -o $@

$(CUDA_DIR)/tests.o: tests/test_cuda.cpp src/life.h src/life_cuda.h Makefile | $(CUDA_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -O3 -DNDEBUG -c $< -o $@

$(CUDA_DIR)/cuda.o: src/life_cuda.cu src/life_cuda.h src/life.h Makefile | $(CUDA_DIR)
	$(NVCC) $(CPPFLAGS) $(CUDA_FLAGS) -c $< -o $@

$(CUDA_DIR)/life: $(CUDA_DIR)/main.o $(CUDA_DIR)/life.o $(CUDA_DIR)/cuda.o
	$(NVCC) $(CUDA_FLAGS) $(CUDA_LINK_FLAGS) $^ -o $@

$(CUDA_DIR)/life_cuda_tests: $(CUDA_DIR)/tests.o $(CUDA_DIR)/life.o $(CUDA_DIR)/cuda.o
	$(NVCC) $(CUDA_FLAGS) $(CUDA_LINK_FLAGS) $^ -o $@

all: debug

debug: $(DEBUG_TARGET) $(TEST_TARGET)

benchmark: $(BENCHMARK_TARGET)

profile: $(PROFILE_TARGET)

test: debug
	$(TEST_TARGET)

$(DEBUG_TARGET): src/main.cpp src/life.cpp src/life.h Makefile | $(DEBUG_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O0 -g src/main.cpp src/life.cpp $(LDFLAGS) -o $@

$(TEST_TARGET): tests/test_life.cpp src/life.cpp src/life.h Makefile | $(DEBUG_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O0 -g tests/test_life.cpp src/life.cpp $(LDFLAGS) -o $@

$(BENCHMARK_TARGET): src/main.cpp src/life.cpp src/life.h Makefile | $(BENCHMARK_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O3 -DNDEBUG src/main.cpp src/life.cpp $(LDFLAGS) -o $@

$(PROFILE_TARGET): src/main.cpp src/life.cpp src/life.h Makefile | $(PROFILE_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(OPENMP_FLAGS) -O2 -g -pg src/main.cpp src/life.cpp $(LDFLAGS) -pg -o $@

$(DEBUG_DIR) $(BENCHMARK_DIR) $(PROFILE_DIR) $(CUDA_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR) gmon.out
