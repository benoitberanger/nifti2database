CREATE TABLE nifti2database_schema.nifti_json (
	dict jsonb NOT NULL,
	suid varchar(70) NOT NULL,
	patient_name varchar(64) NOT NULL,
	insertion_time timestamptz NOT NULL,
	CONSTRAINT nifti_json_pk PRIMARY KEY (suid)
);

GRANT ALL ON TABLE nifti2database_schema.nifti_json TO nifti2database_app;

select * from nifti2database_schema.nifti_json;

INSERT INTO nifti2database_schema.nifti_json
(dict, seriesinstanceuid, insertion_time)
VALUES('{}', 'abcd', now());

select * from nifti2database_schema.nifti_json;
