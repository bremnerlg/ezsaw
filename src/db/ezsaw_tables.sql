CREATE TYPE auto_body_t AS ENUM('sedan', 'coupe', 'SUV', 'pickup', 'hatchback');
CREATE TYPE measure_unit_t AS ENUM ('sample_number', 'joules', 'newtons', 'mm/s', 'degrees', 'mbar');
CREATE TYPE door_t AS ENUM ('driver_front', 'driver_rear', 'passenger_front', 'passenger_rear', 'rear_hatch', 'hood');

CREATE TABLE vehicles (
    vin varchar(17),
    make text,
    model text,
    body auto_body_t,
    manufacture_date date,
    CONSTRAINT vehicle_pk PRIMARY KEY (vin)
);


CREATE TABLE auto_door_stats (
    auto_door_stat_id bigserial,
    auto_door_stat_name text,
    sampled boolean,
    two_var boolean, /* if false, then the result_x_unit is to be sample_number*/
    result_x numeric,
    result_x_unit measure_unit_t,
    result_y_lower_lim numeric,
    result_y numeric,
    result_y_upper_lim numeric,
    result_y_unit measure_unit_t,
    CONSTRAINT auto_door_stats_pk PRIMARY KEY (auto_door_stat_id)
);

CREATE TABLE steps (
    vin varchar(17) REFERENCES vehicles(vin) ON DELETE CASCADE, 
    door door_t,
    fk_steps_auto_door_stats bigint REFERENCES auto_door_stats(auto_door_stat_id) ON DELETE CASCADE,
    CONSTRAINT steps_pk PRIMARY KEY (vin, door, fk_steps_auto_door_stats)
);

CREATE INDEX idx_steps_fk ON steps(fk_steps_auto_door_stats);

-- ============================================
-- VEHICLES (the cars being tested)
-- ============================================
INSERT INTO vehicles (vin, make, model, body, manufacture_date) VALUES
('1HGCM82633A004352', 'Honda',         'Accord',     'sedan',     '2021-03-15'),
('1FTFW1ET5DFB12345', 'Ford',          'F-150',      'pickup',    '2022-06-22'),
('1G1ZT53826F789012', 'Chevrolet',     'Malibu',     'sedan',     '2020-09-10'),
('JTDKN3DU5C0123456', 'Toyota',        'Camry',      'sedan',     '2021-11-30'),
('5YJ3E1EA5KF456789', 'Tesla',         'Model 3',    'sedan',     '2022-02-28'),
('2T1BURHE0JC123456', 'Toyota',        'Corolla',    'sedan',     '2021-04-17'),
('1N4AL3AP6DC234567', 'Nissan',        'Altima',     'sedan',     '2020-08-05'),
('1VWBT7A36EC345678', 'Volkswagen',    'Passat',     'sedan',     '2021-07-20'),
('3FA6P0H73GR456789', 'Ford',          'Fusion',     'sedan',     '2022-01-12'),
('5NPE34AF3FH567890', 'Hyundai',       'Sonata',     'sedan',     '2020-10-25'),
('1G1ZD5ST5JF678901', 'Chevrolet',     'Cruze',      'sedan',     '2021-05-08'),
('19XFC2F69GE789012', 'Honda',         'Civic',      'sedan',     '2022-03-14'),
('1FADP5AU3DL890123', 'Ford',          'C-Max',      'hatchback', '2020-12-03'),
('3VWFE21C04M901234', 'Volkswagen',    'Jetta',      'sedan',     '2021-08-19'),
('KMHCT4AE5CU012345', 'Hyundai',       'Accent',     'sedan',     '2022-04-21'),
('1G1ZB5ST5HF123456', 'Chevrolet',     'Malibu',     'sedan',     '2020-11-17'),
('WAUDF78E45A234567', 'Audi',          'A4',         'sedan',     '2021-06-29'),
('JTHBK1GG1F2345678', 'Lexus',         'ES',         'sedan',     '2022-05-11'),
('1FA6P0H76G5345678', 'Ford',          'Fusion',     'sedan',     '2020-07-04'),
('5NPDH4AE0DH456789', 'Hyundai',       'Elantra',    'sedan',     '2021-09-26'),
('1HGCR2F37EA567890', 'Honda',         'Accord',     'sedan',     '2022-07-08'),
('1G11A5SL7EF678901', 'Chevrolet',     'Impala',     'sedan',     '2020-06-13'),
('WBA3A5C55CF789012', 'BMW',           '3 Series',   'sedan',     '2021-10-02'),
('JTDKBRFU5G3890123', 'Toyota',        'Prius',      'sedan',     '2022-08-15'),
('3FAFP07Z2YR890123', 'Ford',          'Focus',      'sedan',     '2020-05-21'),
('1N4AB7AP7FN901234', 'Nissan',        'Sentra',     'sedan',     '2021-12-30'),
('5UXKR0C58F0123456', 'BMW',           'X5',         'SUV',       '2022-09-05'),
('1GNSK2E04ER123456', 'Chevrolet',     'Tahoe',      'SUV',       '2020-04-18'),
('JTEBU5JR4F5234567', 'Toyota',        '4Runner',    'SUV',       '2021-02-09'),
('5TDBKRFH9FS234567', 'Toyota',        'Highlander', 'SUV',       '2022-10-23');


-- ============================================
-- AUTO DOOR STATS (measurement definitions)
-- ============================================
-- Striker Alignment: newtons vs mm/s
-- Hinge and Doorcheck Performance: joules vs mm/s
INSERT INTO auto_door_stats (
    auto_door_stat_name, sampled, two_var, result_x, result_x_unit,
    result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit
) VALUES
-- Striker Alignment entries (varying x readings, with y in/out of spec)
('Striker Alignment (Sampled)',                 true, true, 185.4, 'newtons', 100.0,  78.2, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 210.7, 'newtons', 100.0, 162.5, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 243.1, 'newtons', 100.0,  92.8, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 167.5, 'newtons', 100.0,  68.4, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 278.9, 'newtons', 100.0, 145.7, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 156.3, 'newtons', 100.0, 119.4, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 199.8, 'newtons', 100.0,  88.1, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 232.6, 'newtons', 100.0, 173.2, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 174.1, 'newtons', 100.0,  56.9, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 265.4, 'newtons', 100.0, 108.7, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 215.3, 'newtons', 100.0, 182.1, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 188.2, 'newtons', 100.0,  72.5, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 251.7, 'newtons', 100.0, 134.6, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 179.5, 'newtons', 100.0,  95.8, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 224.8, 'newtons', 100.0,  63.2, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 193.4, 'newtons', 100.0, 158.9, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 207.6, 'newtons', 100.0, 112.4, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 246.8, 'newtons', 100.0,  84.7, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 171.2, 'newtons', 100.0, 167.3, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 289.5, 'newtons', 100.0,  98.6, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 162.7, 'newtons', 100.0, 142.1, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 238.4, 'newtons', 100.0,  59.8, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 194.1, 'newtons', 100.0, 175.6, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 218.9, 'newtons', 100.0,  76.3, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 254.2, 'newtons', 100.0, 128.5, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 183.6, 'newtons', 100.0,  91.2, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 227.3, 'newtons', 100.0, 188.4, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 168.8, 'newtons', 100.0,  66.7, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 261.7, 'newtons', 100.0, 154.9, 150.0, 'mm/s'),
('Striker Alignment (Sampled)',                 true, true, 196.5, 'newtons', 100.0,  83.1, 150.0, 'mm/s'),

-- Hinge and Doorcheck Performance entries
('Hinge and Doorcheck Performance (Sampled)',  true, true, 142.7, 'joules',   80.0,  85.4, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 198.3, 'joules',   80.0,  67.1, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 256.1, 'joules',   80.0, 134.8, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 175.9, 'joules',   80.0,  92.3, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 221.4, 'joules',   80.0, 156.2, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 163.8, 'joules',   80.0,  58.7, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 247.5, 'joules',   80.0, 104.1, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 189.2, 'joules',   80.0,  74.6, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 154.6, 'joules',   80.0, 128.3, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 233.7, 'joules',   80.0,  61.9, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 207.4, 'joules',   80.0, 145.5, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 168.9, 'joules',   80.0,  82.1, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 284.2, 'joules',   80.0, 118.4, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 176.3, 'joules',   80.0,  96.7, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 215.8, 'joules',   80.0,  69.2, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 191.5, 'joules',   80.0, 137.8, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 158.2, 'joules',   80.0,  88.9, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 263.4, 'joules',   80.0,  52.6, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 184.7, 'joules',   80.0, 162.4, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 229.1, 'joules',   80.0,  79.3, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 167.4, 'joules',   80.0, 113.7, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 245.6, 'joules',   80.0,  64.8, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 152.9, 'joules',   80.0, 148.2, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 218.5, 'joules',   80.0,  94.5, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 196.3, 'joules',   80.0,  71.2, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 271.8, 'joules',   80.0, 132.6, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 173.1, 'joules',   80.0,  86.4, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 238.7, 'joules',   80.0,  57.9, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 182.4, 'joules',   80.0, 169.1, 120.0, 'mm/s'),
('Hinge and Doorcheck Performance (Sampled)',  true, true, 252.3, 'joules',   80.0,  99.8, 120.0, 'mm/s');


-- ============================================
-- STEPS (ties a vehicle + door to a measurement)
-- ============================================
-- Map each vehicle to a unique combination of (door, auto_door_stat)
INSERT INTO steps (vin, door, fk_steps_auto_door_stats) VALUES
('1HGCM82633A004352',  'driver_front',      1),
('1HGCM82633A004352',  'driver_rear',       2),
('1FTFW1ET5DFB12345',  'passenger_front',   3),
('1FTFW1ET5DFB12345',  'passenger_rear',    4),
('1G1ZT53826F789012',  'driver_front',      5),
('1G1ZT53826F789012',  'driver_rear',       6),
('JTDKN3DU5C0123456',  'passenger_front',   7),
('JTDKN3DU5C0123456',  'passenger_rear',    8),
('5YJ3E1EA5KF456789',  'driver_front',      9),
('5YJ3E1EA5KF456789',  'driver_rear',      10),
('2T1BURHE0JC123456',  'passenger_front',  11),
('2T1BURHE0JC123456',  'passenger_rear',   12),
('1N4AL3AP6DC234567',  'driver_front',     13),
('1N4AL3AP6DC234567',  'driver_rear',      14),
('1VWBT7A36EC345678',  'passenger_front',  15),
('1VWBT7A36EC345678',  'passenger_rear',   16),
('3FA6P0H73GR456789',  'driver_front',     17),
('3FA6P0H73GR456789',  'driver_rear',      18),
('5NPE34AF3FH567890',  'passenger_front',  19),
('5NPE34AF3FH567890',  'passenger_rear',   20),
('1G1ZD5ST5JF678901',  'driver_front',     21),
('1G1ZD5ST5JF678901',  'driver_rear',      22),
('19XFC2F69GE789012',  'passenger_front',  23),
('19XFC2F69GE789012',  'passenger_rear',   24),
('1FADP5AU3DL890123',  'driver_front',     25),
('1FADP5AU3DL890123',  'driver_rear',      26),
('3VWFE21C04M901234',  'passenger_front',  27),
('3VWFE21C04M901234',  'passenger_rear',   28),
('KMHCT4AE5CU012345',  'driver_front',     29),
('KMHCT4AE5CU012345',  'driver_rear',      30),
('1G1ZB5ST5HF123456',  'driver_front',     31),
('1G1ZB5ST5HF123456',  'driver_rear',      32),
('WAUDF78E45A234567',  'passenger_front',  33),
('WAUDF78E45A234567',  'passenger_rear',   34),
('JTHBK1GG1F2345678',  'driver_front',     35),
('JTHBK1GG1F2345678',  'driver_rear',      36),
('1FA6P0H76G5345678',  'passenger_front',  37),
('1FA6P0H76G5345678',  'passenger_rear',   38),
('5NPDH4AE0DH456789',  'driver_front',     39),
('5NPDH4AE0DH456789',  'driver_rear',      40),
('1HGCR2F37EA567890',  'passenger_front',  41),
('1HGCR2F37EA567890',  'passenger_rear',   42),
('1G11A5SL7EF678901',  'driver_front',     43),
('1G11A5SL7EF678901',  'driver_rear',      44),
('WBA3A5C55CF789012',  'passenger_front',  45),
('WBA3A5C55CF789012',  'passenger_rear',   46),
('JTDKBRFU5G3890123',  'driver_front',     47),
('JTDKBRFU5G3890123',  'driver_rear',      48),
('3FAFP07Z2YR890123',  'passenger_front',  49),
('3FAFP07Z2YR890123',  'passenger_rear',   50),
('1N4AB7AP7FN901234',  'driver_front',     51),
('1N4AB7AP7FN901234',  'driver_rear',      52),
('5UXKR0C58F0123456',  'rear_hatch',       53),
('5UXKR0C58F0123456',  'hood',             54),
('1GNSK2E04ER123456',  'rear_hatch',       55),
('1GNSK2E04ER123456',  'hood',             56),
('JTEBU5JR4F5234567',  'rear_hatch',       57),
('JTEBU5JR4F5234567',  'hood',             58),
('5TDBKRFH9FS234567',  'rear_hatch',       59),
('5TDBKRFH9FS234567',  'hood',             60);
