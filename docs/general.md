# General Design of the EZmetro (ADSAW) Automotive Door Statistical Analysis Wizard 

## Basic Idea & Premise of EZ ADSAW
The goal of this program is to present outliers for a given vehicle's door measurement results.

The basic functionality looks like this
1. A menu of possible vehicle makes are displayed to the user.

2. The user selects vehicle make, then is taken through a series of steps where they select the model, model type, door type, VIN of specific vehicle to analyze.

3. The user is taken through a series of datasets pulled from SQL database, then formatted, showing where the vehicle is outside of ideal tolerances for door test resutlts, and gives an explanation for why.

## Modules
There are a few main components to verion 1.0.0 of this CLI implementation.

### 1. Evaluating User Input
The initial design will have the user input the VIN by hand along with the door type (following a key, DF = driver front, PF = passenger front and so on), however for future versions there will be a menu to select make, model, doortype measured, etc. 
It must be checked:
    - If the VIN is valid.
        - If so, are there available data for that vehicle?
        - This will come in the form of an SQL query to VIN field of the steps table (see)
    - Eventually...
        - Are data for a vehicle with that make, model, year available?
    - If the doortype requested is valid.

### 2. Data Retrieval 
The data that is desired now is the graphs for the cases in which a vehicle is outside of ideal tolerances for door test results, but in order to show it, it must be determined where the y values for datasets either exceed the upper tolerance, or fall below the lower tolerance. This will require:
    - 1. Querying the database (see data/pseudo_database) for the VINs found within the steps table.
    - 2. If that VIN is present in the database, then querying for the y values that exceed their respective upper tolerance, or fall below their respective lower tolerance.
    - 3. For the y values that are out-of-tolerance the y step_id and step_name must be stored so the outlier can then be separated by a different colour on the graph.

### 3. Graph/Table Generation
For this step, the outlier dataset will be found by the name of the step where there was in out-of-tolerance y value in step #2. At this point, there will be:
    - 1. A query for all x and y values in that step.
    - 2. A plotting routine of all of the x and y values, along with a graph title for each step.
    - 3. An explanation generation routine (possibly integrating AI eventually??).