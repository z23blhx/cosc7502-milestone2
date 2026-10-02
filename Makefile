CXX ?= g++
CPPFLAGS := -Isrc
WARNINGS := -Wall -Wextra -Wpedantic -Wconversion -Wshadow
CXXFLAGS ?= -std=c++17 $(WARNINGS)
BUILD_DIR := build
DEBUG_DIR := $(BUILD_DIR)/debug
BENCHMARK_DIR := $(BUILD_DIR)/benchmark
PROFILE_DIR := $(BUILD_DIR)/profile
DEBUG_TARGET := $(DEBUG_DIR)/life
TEST_TARGET := $(DEBUG_DIR)/life_tests
BENCHMARK_TARGET := $(BENCHMARK_DIR)/life
PROFILE_TARGET := $(PROFILE_DIR)/life

# Avoid loading an incompatible libstdc++ DLL when several MinGW installations
# appear on a Windows PATH. Rangpur/Linux keeps its normal dynamic toolchain.
ifeq ($(OS),Windows_NT)
LDFLAGS += -static
endif

.PHONY: all debug benchmark profile test clean

all: debug

debug: $(DEBUG_TARGET) $(TEST_TARGET)

benchmark: $(BENCHMARK_TARGET)

profile: $(PROFILE_TARGET)

test: debug
	$(TEST_TARGET)

$(DEBUG_TARGET): src/main.cpp src/life.cpp src/life.h | $(DEBUG_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -O0 -g src/main.cpp src/life.cpp $(LDFLAGS) -o $@

$(TEST_TARGET): tests/test_life.cpp src/life.cpp src/life.h | $(DEBUG_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -O0 -g tests/test_life.cpp src/life.cpp $(LDFLAGS) -o $@

$(BENCHMARK_TARGET): src/main.cpp src/life.cpp src/life.h | $(BENCHMARK_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -O3 -DNDEBUG src/main.cpp src/life.cpp $(LDFLAGS) -o $@

$(PROFILE_TARGET): src/main.cpp src/life.cpp src/life.h | $(PROFILE_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -O2 -g -pg src/main.cpp src/life.cpp $(LDFLAGS) -pg -o $@

$(DEBUG_DIR) $(BENCHMARK_DIR) $(PROFILE_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR) gmon.out
