create table monitoreo(
    filename varchar(80),
    tool varchar(80),
    cutting_depth_ap float,
    tool_diameter_d float,
    diameter_ae float,
    feed_vel_f float,
    revol_N float,
    num_of_inserts_z int,
    feet_per_insert_fz float,
    cut_vel_vc float,
    power float,
    energy float,
    time float,
    distance float
);
COPY monitoreo
FROM '/data/monitoreo.csv' 
DELIMITER ',' 
CSV HEADER
NULL as 'NA';