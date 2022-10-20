/* # Objective
 * nifti2database (python package https://github.com/benoitberanger/nifti2database) purpose is to regroup information about MRI sequences even if their output is multiple series and/or mutliple volumes
 * 1 line in the table = 1 sequence
 *
 * Ex1 : mp2rage
 * Typically, mp2rage output is 4 series of 1 image : <SeriesDescription>_INV1, <SeriesDescription>_INV2, <SeriesDescription>_T1map, <SeriesDescription>_UNI_Image
 * Here, 1 mp2rage sequence will be smartly regrouped into a single line in the table.
 *
 * Ex2 : QSM (multi-echo GRE)
 * Multi-echo GRE with magnitude and phase reconstruction will produce theses images : 1 serie of magnitude images containing all echos, and 1 serie of phase images containing all echos
 * Here, 1 QSM sequence will be regrouped into a single line in the table.
 *
 *
 * # How is works
 *
 * ## Table
 * - dict           (jsonb)     this a JSON
 * - suid           (char)      SeriesInstanceUID, used as primary key
 * - patient_id     (char)      20YY_MM_DD_<PatientName>
 * - insertion_time (timestamp)
 *
 * ## dict
 * 'dict' is a JSON like object. We can access it's fields like this : dict->'RepetitionTime', dict->>'SeriesDescription'
 * '->' and '->>' are different operators. Please refer to the doc and examples bellow.
 *
 *
 * # documentation
 * >>> https://www.postgresql.org/docs/9.5/functions-json.html <<<
 *
 *
 * # Examples
 * See below
 *
 *
 * # Typical 'dict' content
 *
 * The 'dict' jsonb element contains all fields form dcm2niix JSON sidecar. Please just open any .json file next to a .nii to check the general aspect.
 *
 * It also contains some elements from the nifti header that are absent from the JSON, such as the FoV and Resolution
 * - scalar fields :          Mx, My, Mz,  (Mt,)                 Rx, Ry, Rz,  (Rt,)          Fx, Fy, Fz,  (Ft,)
 * - array fields : Matrix = (Mx, My, Mz (, Mt))   Resolution = (Rx, Ry, Rz (, Mt))   FoV = (Fx, Fy, Fz (, Ft))
 * IMPORTANT : the numerical values have been rounded to 3 digits (0.95789316 -> 0.958) for readability and avoid rounding errors
 *
 * And BIDS fields :
 * - tag = anat, func, fmap, ...
 * - suffix = T1w, T1map, MP2RAGE, FLAIR, MEGRE, dwi, sbref, bold, phasediff, ...
 *
 */


-- number of sequence : 1 line in the table is 1 sequence
select count(patient_id) from xdat_search.nifti_json;

-- number of exam
select count(distinct patient_id)  from xdat_search.nifti_json;

-- number of protocol
select count(distinct dict->>'ProcedureStepDescription') from xdat_search.nifti_json;

-- number of mprage
select count(patient_id) from xdat_search.nifti_json where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='number';
-- count different resolution for mprage
select distinct dict->'Resolution', count(*)  from xdat_search.nifti_json
where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='number'
group by dict->'Resolution' order by count desc;

-- number of mp2rage
select count(patient_id) from xdat_search.nifti_json where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='array';
-- count different resolution for mp2rage
select distinct dict->'Resolution', count(*)  from xdat_search.nifti_json
where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='array'
group by dict->'Resolution' order by count desc;

-- histogram of nQSM in each protocol
select dict->>'ProcedureStepDescription' as ProtocolName, count(*) from xdat_search.nifti_json
where dict->>'suffix'='MEGRE' and dict->>'SeriesDescription' ~* 'QSM'
group by dict->>'ProcedureStepDescription' order by count desc ;

-- histogram of 3D space FLAIR
select distinct dict->'Resolution', count(*)  from xdat_search.nifti_json
where dict->>'PulseSequenceName'='tse_vfl' and dict ? 'InversionTime'
group by dict->'Resolution' order by count desc ;

-- histogram of 3D space T2
select distinct dict->'Resolution', count(*)  from xdat_search.nifti_json
where dict->>'PulseSequenceName'='tse_vfl' and not (dict ? 'InversionTime')
group by dict->'Resolution' order by count desc ;

-- MINO-AMN MT check TR
select patient_id, dict->'RepetitionTime', dict->'SeriesDescription', dict->'PulseSequenceDetails' from xdat_search.nifti_json
where dict->>'ProcedureStepDescription' ~ 'MINO' and dict->>'SeriesDescription' ~ 'MT'
order by dict->'RepetitionTime', patient_id ;

-- fetch protocols using GAIN resting-state sequence
select dict->> 'PatientName' from xdat_search.nifti_json where
dict->>'PulseSequenceDetails' ~ 'bold' and
dict->>'Rx'='2.009' and dict->>'Ry'='2.009' and dict->>'Rz'='2' and dict->>'Rt'='1' and dict->>'EchoTime'='0.032' and
dict->>'Ft'='420'  and dict->>'FlipAngle'='50' and dict->>'PhaseEncodingDirection'='j-' and dict->>'ReceiveCoilName'='HeadNeck_64' and dict->>'PixelBandwidth'='2480'
order by dict->> 'PatientName' desc ;
