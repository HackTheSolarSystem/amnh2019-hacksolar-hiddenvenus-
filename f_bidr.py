from attrs_structs import RecordTypes as R

data_annotation_labels = {
    'image' : R.Series(
        image_line_count=R.Integer(2),
        image_line_length=R.Integer(2),
        projection_origin_latitude=R.Single_float(),
        projection_origin_longitude=R.Single_float(),
        reference_point_longitude=R.Single_float(),
        reference_point_latitude=R.Single_float(),
        reference_point_offset_lines=R.Integer(4, signed=True),
        reference_point_offset_pixels=R.Integer(4, signed=True),
        burst_counter=R.Integer(4, signed=True),
        nav_unique_id=R.Fixed_length_string(32)),
    # Not quite true. There's a meaning to these, but haven't
    # programmed it yet. I think I'm going to introduce piping here.
    'processing' : R.Plain_bytes(7),
    'radiometer' : R.Series(
        scet=R.Double_float(),
        latitutde=R.Single_float(),
        longitude=R.Single_float(),
        incidence_angle=R.Single_float(),
        terrain_elevation=R.Single_float(),
        spacecraft_x_coord=R.Single_float(),
        spacecraft_y_coord=R.Single_float(),
        spacecraft_z_coord=R.Single_float(),
        receiver_gain=R.Single_float(),
        receiver_temp=R.Single_float(),
        # Coefficients of a polynomial, with temp_coefficients[0]
        # being coef of x^2, and temp_coefficients[2] being the constant.
        temp_coefficients=3*[R.Single_float()],
        sensor_input_noise_temp=R.Single_float(),
        cable_segment_temps=5*[R.Single_float()],
        cable_segment_losses=5*[R.Single_float()],
        atmostphereic_emission_temp=R.Single_float(),
        atmostphereic_attentuation_factor=R.Single_float(),
        cold_sky_reference_temp=R.Single_float()),
}

annotation_block = R.Series(
        data_class=R.Integer(1),
        data_annotation_label_length=R.Integer(8)
        )

orbit_number = R.Integer(2)
secondary_header = R.Series(
        BIDR_secondary_label_type=R.Integer(2),
        BIDR_secondary_label_length=R.Integer(2),
        )
logcal_record = R.Series(
        NJPL_primary_label_type=R.Fixed_length_string(12),
        NJPL_primary_label_length=R.Ascii_integer(8),
        )
