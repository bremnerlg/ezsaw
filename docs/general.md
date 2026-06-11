# General Design of the EZmetro (ADSAW) Automotive Door Statistical Analysis Wizard 

## Basic Idea & Premise of EZ ADSAW
The goal of this program is to present outliers for a given vehicle's door measurement results.

The basic functionality looks like this
1. A menu of possible vehicle makes are displayed to the user.

2. The user selects vehicle make, then is taken through a series of steps where they select the model, model type, door type, VIN of specific vehicle to analyze.

3. The user is taken through a series of tables pulled from a CSV file, then formatted, (placeholder for the GUI which will show graphs) showing where the vehicle is outside of ideal tolerances for door test resutlts, and gives an explanation for why.

## Modules
There are a few main components to verion 1.0.0 of this CLI implementation.

1. A CSV file parser that uses iostream to convert csv elements to their respective data type (std::string, int, float, enum) and structure them in a table class with rows and columns.

2. See what test results are available for a given vehicle entry.

3. Check each recorded test case ("step") for the vehicle, and see if it falls outside of the tolerances. (Initally find fixed tolerances, later implement a system to calculated 2sigma sampled tolerances).

4. Print a formatted table with an -----> pointing towards the outlier result, then give an explanation of a likely cause.

5. An interface to read in vehicle information, and step through the outlier cases for a given entry.
