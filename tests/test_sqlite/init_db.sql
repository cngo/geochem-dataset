CREATE TABLE config (
	id INTEGER NOT NULL,
	name VARCHAR,
	value VARCHAR,
	PRIMARY KEY (id),
	UNIQUE (name)
);


CREATE TABLE datasets (
	id INTEGER NOT NULL,
	name VARCHAR,
    "extra" text,
	PRIMARY KEY (id),
	UNIQUE (name)
);


CREATE TABLE documents (
	id INTEGER NOT NULL,
	dataset_id INTEGER,
	recommended_citation VARCHAR,
    "extra" text,
	PRIMARY KEY (id),
	UNIQUE (dataset_id, recommended_citation),
	FOREIGN KEY(dataset_id) REFERENCES datasets (id)
);


CREATE TABLE surveys (
	id INTEGER NOT NULL,
	dataset_id INTEGER,
	title VARCHAR,
	organization VARCHAR,
	year_begin INTEGER,
	year_end INTEGER,
	party_leader VARCHAR,
	description VARCHAR,
	gsc_catalog_number INTEGER,
    "extra" text,
	PRIMARY KEY (id),
	UNIQUE (dataset_id, title),
	FOREIGN KEY(dataset_id) REFERENCES datasets (id),
    CHECK ((year_begin IS NULL AND year_end IS NULL) OR (year_begin IS NOT NULL AND (year_end IS NULL OR year_end >= year_begin)))
);


CREATE TABLE samples (
	id INTEGER NOT NULL,
	survey_id INTEGER,
	station VARCHAR,
	earthmat VARCHAR,
	name VARCHAR,
	lat_nad27 FLOAT,
	long_nad27 FLOAT,
	lat_nad83 FLOAT,
	long_nad83 FLOAT,
	x_nad27 FLOAT,
	y_nad27 FLOAT,
	x_nad83 FLOAT,
	y_nad83 FLOAT,
	zone VARCHAR,
	earthmat_type VARCHAR,
	status VARCHAR,
    "extra" text,
	PRIMARY KEY (id),
	UNIQUE (survey_id, station, earthmat, name),
	FOREIGN KEY(survey_id) REFERENCES surveys (id),
    CHECK ((lat_nad27 IS NULL AND long_nad27 IS NULL) OR (lat_nad27 IS NOT NULL AND long_nad27 IS NOT NULL)),
    CHECK ((lat_nad83 IS NULL AND long_nad83 IS NULL) OR (lat_nad83 IS NOT NULL AND long_nad83 IS NOT NULL)),
    CHECK ((x_nad27 IS NULL AND y_nad27 IS NULL) OR (x_nad27 IS NOT NULL AND y_nad27 IS NOT NULL)),
    CHECK ((x_nad83 IS NULL AND y_nad83 IS NULL) OR (x_nad83 IS NOT NULL AND y_nad83 IS NOT NULL))
);


CREATE TABLE subsamples (
	id INTEGER NOT NULL,
	sample_id INTEGER,
	parent_id INTEGER,
	name VARCHAR,
    "extra" text,
	PRIMARY KEY (id),
	UNIQUE (sample_id, parent_id, name),
	FOREIGN KEY(sample_id) REFERENCES samples (id),
	FOREIGN KEY(parent_id) REFERENCES subsamples (id)
);


CREATE TABLE metadata_sets (
    id INTEGER NOT NULL,
	dataset_id INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(dataset_id) REFERENCES datasets (id)
);


CREATE TABLE metadata_types (
    id INTEGER NOT NULL,
    dataset_id INTEGER,
    name VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY(dataset_id) REFERENCES datasets (id),
    UNIQUE (name)
);


CREATE TABLE metadata (
    id INTEGER NOT NULL,
    metadata_set_id INTEGER,
    metadata_type_id INTEGER,
    "value" TEXT,
    PRIMARY KEY (id),
    UNIQUE (metadata_set_id, metadata_type_id),
    FOREIGN KEY(metadata_set_id) REFERENCES metadata_sets (id),
    FOREIGN KEY(metadata_type_id) REFERENCES metadata_types (id)
);


CREATE TABLE result_types (
    id INTEGER NOT NULL,
    dataset_id INTEGER,
    name VARCHAR,
    PRIMARY KEY (id)
    FOREIGN KEY(dataset_id) REFERENCES datasets (id),
    UNIQUE (name)
);


CREATE TABLE results (
    id INTEGER NOT NULL,
    subsample_id INTEGER,
    result_type_id INTEGER,
    metadata_set_id INTEGER,
    "value" VARCHAR,
    "extra" text,
    PRIMARY KEY (id),
    FOREIGN KEY(subsample_id) REFERENCES subsamples (id),
    FOREIGN KEY(result_type_id) REFERENCES result_types (id),
    FOREIGN KEY(metadata_set_id) REFERENCES metadata_sets (id),
    UNIQUE (id, subsample_id, result_type_id, metadata_set_id)
);
