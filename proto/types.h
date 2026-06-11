/* Enumerations of recurring categories in datasets */

enum class DoorType {
	DRIVER_FRONT, DRIVER_REAR, TRUNK, PASSENGER_REAR, PASSENGER_FRONT, HOOD
};

enum class TolType {
	FIXED, SAMPLED
};

enum class MeasureType {
	FORCE = 1, SPEED, ENERGY, ANGLE, PRESSURE
};

enum class Unit {
	JOULE = 6, MM_SEC, NEWTON, DEG, MBAR, DEGREE
};
