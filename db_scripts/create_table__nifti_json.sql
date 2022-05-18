CREATE TABLE nifti2database_schema.nifti_json (
	dict jsonb NOT NULL,
	suid varchar(128) NOT NULL,
	patient_id varchar(128) NOT NULL,
	insertion_time timestamptz NOT NULL,
	CONSTRAINT nifti_json_pk PRIMARY KEY (suid)
);

GRANT ALL ON TABLE nifti2database_schema.nifti_json TO nifti2database_app;

select * from nifti2database_schema.nifti_json;

INSERT INTO nifti2database_schema.nifti_json
(dict, suid, patient_id, insertion_time)
VALUES('{}', '0.0.0.0', '2022_01_01_DEV2_XXX', now());

select * from nifti2database_schema.nifti_json;

-- delete from nifti2database_schema.nifti_json;
