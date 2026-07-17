-- ============================================================================
-- Outlier Introduction Script
-- ============================================================================
-- This script introduces realistic outliers into the auto_door_stats data.
-- Instead of purely random extreme values, it uses values offset by
-- 2-5 standard deviations from the expected mean (midpoint of the
-- acceptable range), with variance depending on door location.
--
-- Some doors (driver_front, hood) have tighter tolerances, while others
-- (rear_hatch, passenger_rear) show more variance in real-world data.
-- ============================================================================

BEGIN;

DO $$
DECLARE
  rec RECORD;
  r double precision;
  sigma_mult double precision;
  range_width numeric;
  mid_point numeric;
  new_y numeric;
  door_variance_factor double precision;
  row_idx int := 0;
  systematic_cnt int := 0;
  subtle_cnt int := 0;
  extreme_cnt int := 0;
BEGIN

  -- Phase 1: Systematic outliers — one targeted stat per (VIN, door) block
  -- We pick stat #3 (Hinge Bind) which is a common real-world failure point.
  -- Each outlier deviates 2-5σ from the range midpoint, tuned by door.

  FOR rec IN
    SELECT s.vin, s.door, s.fk_steps_auto_door_stats,
           a.result_y_lower_lim, a.result_y, a.result_y_upper_lim,
           ROW_NUMBER() OVER (PARTITION BY s.vin, s.door ORDER BY s.fk_steps_auto_door_stats) AS rn
    FROM steps s
    JOIN auto_door_stats a ON s.fk_steps_auto_door_stats = a.auto_door_stat_id
    ORDER BY s.vin, s.door, s.fk_steps_auto_door_stats
  LOOP
    row_idx := row_idx + 1;

    -- Only target stat #3 (Hinge Bind) in every VIN/door block
    IF rec.rn != 3 THEN
      CONTINUE;
    END IF;

    range_width := rec.result_y_upper_lim - rec.result_y_lower_lim;
    mid_point := rec.result_y_lower_lim + (range_width / 2);

    -- Door-specific variance factor: some doors have more natural variance
    CASE rec.door
      WHEN 'driver_front'  THEN door_variance_factor := 1.0;   -- tightest tolerance
      WHEN 'driver_rear'   THEN door_variance_factor := 1.2;
      WHEN 'passenger_front' THEN door_variance_factor := 1.1;
      WHEN 'passenger_rear'  THEN door_variance_factor := 1.4; -- more slack
      WHEN 'rear_hatch'    THEN door_variance_factor := 1.6;   -- hatch doors vary most
      WHEN 'hood'          THEN door_variance_factor := 0.9;   -- hoods are consistent
      ELSE door_variance_factor := 1.0;
    END CASE;

    -- Random sigma multiplier between 2.0 and 5.0
    sigma_mult := 2.0 + (random() * 3.0);

    -- The standard deviation is estimated as range/6 (assuming ±3σ covers the range)
    r := random();
    IF r < 0.5 THEN
      -- Below lower limit: mid_point - sigma_mult * (range_width / 6) * door_variance_factor
      new_y := mid_point - (sigma_mult * (range_width / 6.0) * door_variance_factor);
    ELSE
      -- Above upper limit
      new_y := mid_point + (sigma_mult * (range_width / 6.0) * door_variance_factor);
    END IF;

    -- Clamp: ensure it's actually outside the acceptable range
    IF new_y BETWEEN rec.result_y_lower_lim AND rec.result_y_upper_lim THEN
      IF r < 0.5 THEN
        new_y := rec.result_y_lower_lim - (range_width * 0.1 * door_variance_factor);
      ELSE
        new_y := rec.result_y_upper_lim + (range_width * 0.1 * door_variance_factor);
      END IF;
    END IF;

    UPDATE auto_door_stats
    SET result_y = new_y
    WHERE auto_door_stat_id = rec.fk_steps_auto_door_stats;

    systematic_cnt := systematic_cnt + 1;
  END LOOP;

  RAISE NOTICE 'Systematic outliers (1 per VIN/door block): %', systematic_cnt;

  -- Phase 2: Subtle outliers (barely outside the range — 0.5-2% beyond limit)
  -- These simulate marginal failures that are easy to miss.

  UPDATE auto_door_stats
  SET result_y = result_y_upper_lim + (result_y_upper_lim * (0.005 + random() * 0.02))
  WHERE random() < 0.03
    AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

  GET DIAGNOSTICS subtle_cnt = ROW_COUNT;

  UPDATE auto_door_stats
  SET result_y = GREATEST(0, result_y_lower_lim - (result_y_lower_lim * (0.005 + random() * 0.02)))
  WHERE random() < 0.03
    AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

  subtle_cnt := subtle_cnt + ROW_COUNT;

  RAISE NOTICE 'Subtle boundary outliers added: %', subtle_cnt;

  -- Phase 3: Extreme outliers (5-8σ, very rare — ~0.5% chance)
  -- These simulate catastrophic sensor failures or severe damage.

  UPDATE auto_door_stats
  SET result_y = result_y_upper_lim + (result_y_upper_lim * (2.0 + random() * 4.0))
  WHERE random() < 0.005
    AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

  GET DIAGNOSTICS extreme_cnt = ROW_COUNT;

  UPDATE auto_door_stats
  SET result_y = GREATEST(0, result_y_lower_lim - (result_y_lower_lim * (2.0 + random() * 4.0)))
  WHERE random() < 0.005
    AND result_y BETWEEN result_y_lower_lim AND result_y_upper_lim;

  extreme_cnt := extreme_cnt + ROW_COUNT;

  RAISE NOTICE 'Extreme outliers added: %', extreme_cnt;

END $$;

-- ============================================================================
-- Summary: outliers per door location
-- ============================================================================

SELECT
  st.door,
  COUNT(*) FILTER (WHERE a.result_y < a.result_y_lower_lim) AS below_lower,
  COUNT(*) FILTER (WHERE a.result_y > a.result_y_upper_lim) AS above_upper,
  COUNT(*) FILTER (WHERE a.result_y < a.result_y_lower_lim OR a.result_y > a.result_y_upper_lim) AS total_outliers
FROM steps st
JOIN auto_door_stats a ON st.fk_steps_auto_door_stats = a.auto_door_stat_id
GROUP BY st.door
ORDER BY st.door;

-- ============================================================================
-- Overall verification
-- ============================================================================

SELECT 'outliers_found' AS info, COUNT(*) AS count
FROM auto_door_stats
WHERE result_y < result_y_lower_lim OR result_y > result_y_upper_lim;

SELECT 'total_stats' AS info, COUNT(*) AS count
FROM auto_door_stats;

COMMIT;
