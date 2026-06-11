cmake_minimum_required(VERSION 3.23)

project(ezsaw_proto1)
add_executable(ezsaw_proto1)

target_sources(ezsaw_proto1
	PRIVATE
		main.cpp
		door_entry.cpp
)
