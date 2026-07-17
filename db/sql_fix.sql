-- Comprehensive fix for auto_door_stats data

BEGIN;

-- Step 1: Map old IDs to new IDs following stat_ordering.json order
CREATE TEMP TABLE id_map AS
WITH stats_with_block AS (
  SELECT 
    auto_door_stat_id as old_id,
    (auto_door_stat_id - 1) / 9 as block_num,
    CASE (auto_door_stat_id - 1) % 9
      WHEN 0 THEN 1  WHEN 1 THEN 4  WHEN 2 THEN 8
      WHEN 3 THEN 9  WHEN 4 THEN 2  WHEN 5 THEN 3
      WHEN 6 THEN 5  WHEN 7 THEN 7  WHEN 8 THEN 6
    END as new_pos
  FROM auto_door_stats
)
SELECT old_id, block_num * 9 + new_pos as new_id FROM stats_with_block;

-- Step 2: Create reordered stats table
CREATE TABLE auto_door_stats_new AS
SELECT m.new_id as auto_door_stat_id, s.auto_door_stat_name, s.sampled, s.two_var,
       s.result_x, s.result_x_unit, s.result_y_lower_lim, s.result_y,
       s.result_y_upper_lim, s.result_y_unit
FROM auto_door_stats s
JOIN id_map m ON s.auto_door_stat_id = m.old_id
ORDER BY m.new_id;

CREATE INDEX idx_stats_new_name ON auto_door_stats_new(auto_door_stat_name);

-- Step 3: Create reordered steps table
CREATE TABLE steps_new AS
SELECT s.vin, s.door, m.new_id as fk_steps_auto_door_stats
FROM steps s
JOIN id_map m ON s.fk_steps_auto_door_stats = m.old_id;

CREATE INDEX idx_steps_new_vin ON steps_new(vin, door);
CREATE INDEX idx_steps_new_fk ON steps_new(fk_steps_auto_door_stats);

-- Step 4: Add missing SUV passenger doors + hatchback rear_hatch
DO $$
DECLARE
  v_vin text;
  v_door text;
  v_new_stat_id bigint;
  v_pos integer;
  -- stat_names, sampled, two_var aligned with STAT_ORDERING positions
  stat_names text[] := ARRAY[
    'Striker Alignment (Sampled)', 'Hinge Inclination (Sampled)',
    'Hinge Bind (Sampled)', 'Hinge and Doorcheck Performance (Sampled)',
    'Door Check Performance No Cabin (Sampled)', 'Seal Dynamics (Sampled)',
    'Static Closing Force (Sampled)', 'Closing Energy from First Position (Sampled)',
    'Closing Energy from Full Open (Sampled)'
  ];
  two_var_vals boolean[] := ARRAY[true, false, false, true, false, false, false, false, false];
  x_units text[] := ARRAY['newtons', NULL, NULL, 'newtons', NULL, NULL, NULL, NULL, NULL];
  y_units text[] := ARRAY['mm/s', 'degrees', 'newtons', 'newtons', 'newtons', 'newtons', 'newtons', 'joules', 'joules'];
  avg_x numeric[] := ARRAY[223.8, NULL, NULL, 201.5, NULL, NULL, NULL, NULL, NULL];
  std_x numeric[] := ARRAY[42.9, NULL, NULL, 58.1, NULL, NULL, NULL, NULL, NULL];
  avg_lo numeric[] := ARRAY[74.8, 2.6, 9.4, 65.6, 5.7, 14.2, 8.8, 2.0, 1.9];
  std_lo numeric[] := ARRAY[25.9, 1.6, 5.6, 24.2, 3.4, 5.7, 4.0, 0.9, 0.9];
  avg_y numeric[] := ARRAY[124.6, 5.4, 23.0, 109.4, 13.7, 31.8, 20.3, 4.6, 4.5];
  std_y numeric[] := ARRAY[43.1, 3.1, 12.1, 40.3, 7.4, 13.1, 8.9, 2.0, 2.1];
  avg_up numeric[] := ARRAY[174.4, 8.2, 40.8, 153.1, 24.6, 55.7, 35.9, 8.1, 8.1];
  std_up numeric[] := ARRAY[60.3, 4.7, 21.7, 56.4, 13.4, 22.9, 16.2, 3.6, 3.7];
  gen_x numeric; gen_lo numeric; gen_y numeric; gen_up numeric;
BEGIN
  SELECT COALESCE(MAX(auto_door_stat_id), 0) INTO v_new_stat_id FROM auto_door_stats_new;
  
  -- SUV passenger doors
  FOR v_vin IN SELECT vin FROM vehicles WHERE body = 'SUV' ORDER BY vin LOOP
    FOREACH v_door IN ARRAY ARRAY['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'] LOOP
      FOR v_pos IN 1..9 LOOP
        v_new_stat_id := v_new_stat_id + 1;
        IF two_var_vals[v_pos] THEN
          gen_x := ROUND((avg_x[v_pos] + (random() - 0.5) * std_x[v_pos])::numeric, 1);
        ELSE
          gen_x := v_new_stat_id / 9;
        END IF;
        gen_lo := GREATEST(0.1, ROUND((avg_lo[v_pos] + (random() - 0.5) * std_lo[v_pos])::numeric, 1));
        gen_y  := GREATEST(0.1, ROUND((avg_y[v_pos]  + (random() - 0.5) * std_y[v_pos])::numeric, 1));
        gen_up := ROUND((avg_up[v_pos] + (random() - 0.5) * std_up[v_pos])::numeric, 1);
        IF gen_lo >= gen_y THEN gen_lo := gen_y - 0.2; END IF;
        IF gen_lo < 0.01 THEN gen_lo := 0.1; END IF;
        IF gen_y >= gen_up THEN gen_up := gen_y + 0.5; END IF;
        
        INSERT INTO auto_door_stats_new VALUES (
          v_new_stat_id, stat_names[v_pos], two_var_vals[v_pos], two_var_vals[v_pos],
          gen_x,
          CASE WHEN x_units[v_pos] IS NOT NULL THEN x_units[v_pos]::measure_unit_t ELSE NULL END,
          gen_lo, gen_y, gen_up,
          CASE WHEN y_units[v_pos] IS NOT NULL THEN y_units[v_pos]::measure_unit_t ELSE NULL END
        );
        INSERT INTO steps_new VALUES (v_vin, v_door::door_t, v_new_stat_id);
      END LOOP;
    END LOOP;
  END LOOP;

  -- hatchback rear_hatch
  FOR v_vin IN SELECT vin FROM vehicles WHERE body = 'hatchback' LOOP
    FOR v_pos IN 1..9 LOOP
      v_new_stat_id := v_new_stat_id + 1;
      IF two_var_vals[v_pos] THEN
        gen_x := ROUND((avg_x[v_pos] + (random() - 0.5) * std_x[v_pos])::numeric, 1);
      ELSE
        gen_x := v_new_stat_id / 9;
      END IF;
      gen_lo := GREATEST(0.1, ROUND((avg_lo[v_pos] + (random() - 0.5) * std_lo[v_pos])::numeric, 1));
      gen_y  := GREATEST(0.1, ROUND((avg_y[v_pos]  + (random() - 0.5) * std_y[v_pos])::numeric, 1));
      gen_up := ROUND((avg_up[v_pos] + (random() - 0.5) * std_up[v_pos])::numeric, 1);
      IF gen_lo >= gen_y THEN gen_lo := gen_y - 0.2; END IF;
      IF gen_lo < 0.01 THEN gen_lo := 0.1; END IF;
      IF gen_y >= gen_up THEN gen_up := gen_y + 0.5; END IF;
      
      INSERT INTO auto_door_stats_new VALUES (
        v_new_stat_id, stat_names[v_pos], two_var_vals[v_pos], two_var_vals[v_pos],
        gen_x,
        CASE WHEN x_units[v_pos] IS NOT NULL THEN x_units[v_pos]::measure_unit_t ELSE NULL END,
        gen_lo, gen_y, gen_up,
        CASE WHEN y_units[v_pos] IS NOT NULL THEN y_units[v_pos]::measure_unit_t ELSE NULL END
      );
      INSERT INTO steps_new VALUES (v_vin, 'rear_hatch'::door_t, v_new_stat_id);
    END LOOP;
  END LOOP;
END $$;

-- Step 5: Swap tables
DROP TABLE auto_door_stats CASCADE;
ALTER TABLE auto_door_stats_new RENAME TO auto_door_stats;
DROP TABLE steps CASCADE;
ALTER TABLE steps_new RENAME TO steps;

-- Step 6: Re-add constraints
ALTER TABLE auto_door_stats ADD PRIMARY KEY (auto_door_stat_id);
ALTER TABLE steps ADD FOREIGN KEY (fk_steps_auto_door_stats) REFERENCES auto_door_stats(auto_door_stat_id);
ALTER TABLE steps ADD FOREIGN KEY (vin) REFERENCES vehicles(vin);

-- Recreate sequence (was dropped with table CASCADE)
CREATE SEQUENCE auto_door_stats_auto_door_stat_id_seq;
SELECT setval('auto_door_stats_auto_door_stat_id_seq', COALESCE(MAX(auto_door_stat_id), 0))
FROM auto_door_stats;
ALTER TABLE auto_door_stats ALTER COLUMN auto_door_stat_id
  SET DEFAULT nextval('auto_door_stats_auto_door_stat_id_seq');
ALTER SEQUENCE auto_door_stats_auto_door_stat_id_seq OWNED BY auto_door_stats.auto_door_stat_id;

-- Verification
SELECT 'STATS: ' || COUNT(*) FROM auto_door_stats;
SELECT 'STEPS: ' || COUNT(*) FROM steps;
SELECT 'swapped: ' || COUNT(*) FROM auto_door_stats WHERE result_y_lower_lim > result_y_upper_lim;
SELECT 'outliers: ' || COUNT(*) FROM auto_door_stats WHERE result_y < result_y_lower_lim OR result_y > result_y_upper_lim;
SELECT v.body, s.door, COUNT(DISTINCT v.vin) as vins
FROM vehicles v JOIN steps s ON v.vin = s.vin
GROUP BY v.body, s.door ORDER BY v.body, s.door;
SELECT auto_door_stat_id, auto_door_stat_name, two_var, result_x, result_y_lower_lim, result_y, result_y_upper_lim
FROM auto_door_stats WHERE auto_door_stat_id IN (1,2,3,4,5) ORDER BY auto_door_stat_id;

COMMIT;
