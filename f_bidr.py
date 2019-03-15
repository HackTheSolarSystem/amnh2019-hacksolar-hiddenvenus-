from attrs_structs import RecordTypes as R

data_annotation_labels = {
    'image' : R.Series(
        image_line_count=R.Integer(2),
        image_line_length=R.Integer(2),
        projection_origin_latitude=R.Float('single'),
        projection_origin_longitude=R.Float('single'),
        reference_point_longitude=R.Float('single'),
        reference_point_latitude=R.Float('single'),
        reference_point_offset_lines=R.Integer(4, signed=True),
        reference_point_offset_pixels=R.Integer(4, signed=True),
        burst_counter=R.Integer(4, signed=True),
        nav_unique_id=R.Fixed_length_string(32)),
    # Not quite true. There's a meaning to these, but it works on a
    # bit level, not a byte level. I think I'm going to introduce
    # piping here. However the total length is actually 7 bytes.
    'processing' : R.Plain_bytes(7),
    # Actually longer. 112 bytes. This only covers 88 bytes. Remaining
    # bytes are unused.
    'radiometer' : R.Series(
        scet=R.Float('double'),
        latitutde=R.Float('single'),
        longitude=R.Float('single'),
        incidence_angle=R.Float('single'),
        terrain_elevation=R.Float('single'),
        spacecraft_x_coord=R.Float('single'),
        spacecraft_y_coord=R.Float('single'),
        spacecraft_z_coord=R.Float('single'),
        receiver_gain=R.Float('single'),
        receiver_temp=R.Float('single'),
        # Coefficients of a polynomial, with temp_coefficients[0]
        # being coef of x^2, and temp_coefficients[2] being the constant.
        temp_coefficients=R.List(3*[R.Float('single')]),
        sensor_input_noise_temp=R.Float('single'),
        cable_segment_temps=R.List(5*[R.Float('single')]),
        cable_segment_losses=R.List(5*[R.Float('single')]),
        atmostphereic_emission_temp=R.Float('single'),
        atmostphereic_attentuation_factor=R.Float('single'),
        cold_sky_reference_temp=R.Float('single')),
}

data_blocks = {
    # Format covered in appendix D. 512 bytes long.
    'per_orbit' : R.Series(
        orbit_number=R.Float('single'),
        mapping_start_time=R.Float('double'),
        mapping_stop_time=R.Float('double'),
        total_bursts_on_orbit=R.Integer(4),
        product_id=R.Fixed_length_string(9),
        volume_id=R.Fixed_length_string(6),
        wall_clock_time_of_start=R.Fixed_length_string(19),
        number_of_looks_used=R.Integer(4),
        left_or_right_looking=R.Integer(4),
        nav_unique_id=R.Fixed_length_string(32),
        # This is not quite true. This is a special format of time.
        periapsis_time=R.Fixed_length_string(15),


}
annotation_block = R.Series(
        data_class=R.Integer(1),
        data_annotation_label_length=R.Integer(8)
        )

orbit_number = R.Integer(2)
secondary_header = R.Series(
        BIDR_secondary_label_type=R.Integer(2),
        BIDR_secondary_label_length=R.Integer(2),
        orbit_number=orbit_number,
        )
logcal_record = R.Series(
        NJPL_primary_label_type=R.Fixed_length_string(12),
        NJPL_primary_label_length=R.Ascii_integer(8),
        )
