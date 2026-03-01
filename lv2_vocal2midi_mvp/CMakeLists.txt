cmake_minimum_required(VERSION 3.16)
project(vocal2midi_lv2_mvp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(LV2 REQUIRED IMPORTED_TARGET lv2)

add_library(vocal2midi_lv2 MODULE
  src/plugin.cpp
)

target_link_libraries(vocal2midi_lv2 PRIVATE PkgConfig::LV2)

target_compile_options(vocal2midi_lv2 PRIVATE -Wall -Wextra -Wpedantic)

set_target_properties(vocal2midi_lv2 PROPERTIES
  PREFIX ""
  OUTPUT_NAME "vocal2midi"
)

set(LV2_BUNDLE_DIR "${CMAKE_BINARY_DIR}/vocal2midi.lv2")

add_custom_command(TARGET vocal2midi_lv2 POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${LV2_BUNDLE_DIR}"
  COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:vocal2midi_lv2>" "${LV2_BUNDLE_DIR}/vocal2midi.so"
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_SOURCE_DIR}/lv2/vocal2midi.lv2/manifest.ttl" "${LV2_BUNDLE_DIR}/manifest.ttl"
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_SOURCE_DIR}/lv2/vocal2midi.lv2/vocal2midi.ttl" "${LV2_BUNDLE_DIR}/vocal2midi.ttl"
)

install(TARGETS vocal2midi_lv2 LIBRARY DESTINATION lib/lv2/vocal2midi.lv2)
install(FILES
  lv2/vocal2midi.lv2/manifest.ttl
  lv2/vocal2midi.lv2/vocal2midi.ttl
  DESTINATION lib/lv2/vocal2midi.lv2
)
