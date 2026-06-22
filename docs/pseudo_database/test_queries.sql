SELECT * FROM steps;
SELECT * FROM vehicles;
WHERE vin = 'WDDGF4HB6ER123456';

SELECT make, model, manufacture_date 
FROM vehicles
ORDER BY manufacture_date DESC;

ALTER TABLE steps DROP COLUMN for_vin;
ALTER TABLE steps ADD COLUMN step_id serial;
ALTER TABLE steps DROP COLUMN id;
ALTER TABLE steps ADD COLUMN vin varchar(17);

-- TODO: Create a foreign key for steps linking it to vehicles, allow a VIN to be used for multiple steps.


SELECT *
FROM steps JOIN vehicles
ON steps.vin = vehicles.vin;
