CREATE TABLE nifti2database_schema.nifti_json (
	"json" jsonb NULL,
	seriesinstanceuid varchar(70) NOT NULL,
	insertion_time time(0) NOT NULL
);

select * from nifti2database_schema.nifti_json;

INSERT INTO nifti2database_schema.nifti_json
("json", seriesinstanceuid, insertion_time)
VALUES('{}', 'abcd', now());

select * from nifti2database_schema.nifti_json;

