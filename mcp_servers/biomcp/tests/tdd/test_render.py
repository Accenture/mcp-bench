from biomcp import render


def test_render_full_json(data_dir):
    input_data = (data_dir / "ct_gov/trials_NCT04280705.json").read_text()
    expect_markdown = (data_dir / "ct_gov/trials_NCT04280705.txt").read_text()
    markdown = render.to_markdown(input_data)
    assert markdown == expect_markdown

    input_data = (
        data_dir / "myvariant/variants_full_braf_v600e.json"
    ).read_text()
    expect_markdown = (
        data_dir / "myvariant/variants_full_braf_v600e.txt"
    ).read_text()
    markdown = render.to_markdown(input_data)
    print("==" * 100)
    print(markdown)
    print("==" * 100)
    assert markdown == expect_markdown


def test_render_with_nones():
    markdown = render.to_markdown(data)
    assert (
        markdown
        == """# Studies

## Protocol Section

### Design Module
Study Type: interventional
Phases: phase2

### Identification Module
Brief Title:
  study of autologous tumor infiltrating lymphocytes in patients with
  solid tumors
Nct Id: nct03645928

### Status Module
Overall Status: recruiting

#### Completion Date Struct
Date: 2029-08-09

#### Start Date Struct
Date: 2019-05-07
"""
    )


data = {
    "next_page_token": None,
    "studies": [
        {
            "derived_section": None,
            "document_section": None,
            "has_results": None,
            "protocol_section": {
                "arms_interventions_module": None,
                "conditions_module": None,
                "contacts_locations_module": None,
                "description_module": None,
                "design_module": {
                    "design_info": None,
                    "enrollment_info": None,
                    "phases": ["phase2"],
                    "study_type": "interventional",
                },
                "eligibility_module": None,
                "identification_module": {
                    "acronym": None,
                    "brief_title": "study "
                    "of "
                    "autologous "
                    "tumor "
                    "infiltrating "
                    "lymphocytes "
                    "in "
                    "patients "
                    "with "
                    "solid "
                    "tumors",
                    "nct_id": "nct03645928",
                    "official_title": None,
                    "org_study_id_info": None,
                    "organization": None,
                    "secondary_id_infos": None,
                },
                "outcomes_module": None,
                "oversight_module": None,
                "references_module": None,
                "sponsor_collaborators_module": None,
                "status_module": {
                    "completion_date_struct": {
                        "date": "2029-08-09",
                        "type": None,
                    },
                    "expanded_access_info": None,
                    "last_known_status": None,
                    "last_update_post_date_struct": None,
                    "last_update_submit_date": None,
                    "overall_status": "recruiting",
                    "primary_completion_date_struct": None,
                    "results_first_post_date_struct": None,
                    "results_first_submit_date": None,
                    "results_first_submit_qc_date": None,
                    "start_date_struct": {"date": "2019-05-07", "type": None},
                    "status_verified_date": None,
                    "study_first_post_date_struct": None,
                    "study_first_submit_date": None,
                    "study_first_submit_qc_date": None,
                    "why_stopped": None,
                },
            },
            "results_section": None,
        },
    ],
}


def test_transform_key_protocol_section():
    assert render.transform_key("protocol_section") == "Protocol Section"


def test_transform_key_nct_number():
    assert render.transform_key("nct_number") == "Nct Number"


def test_transform_key_study_url():
    assert render.transform_key("study_url") == "Study Url"


def test_transform_key_allcaps():
    assert render.transform_key("allcaps") == "Allcaps"


def test_transform_key_primary_purpose():
    assert render.transform_key("primary_purpose") == "Primary Purpose"


def test_transform_key_underscores():
    assert render.transform_key("some_key_name") == "Some Key Name"


def test_transform_key_lowercase():
    assert render.transform_key("somekey") == "Somekey"


def test_transform_key_nctid():
    assert render.transform_key("nct_id") == "Nct Id"


def test_transform_key_4dct():
    assert render.transform_key("4dct") == "4dct"


def test_wrap_preserve_newlines_blank():
    assert render.wrap_preserve_newlines("", 20) == []


def test_wrap_preserve_newlines_short_line():
    text = "hello world"
    assert render.wrap_preserve_newlines(text, 20) == ["hello world"]


def test_wrap_preserve_newlines_long():
    text = "this line is definitely longer than twenty characters"
    lines = render.wrap_preserve_newlines(text, 20)
    assert len(lines) > 1
    assert "this line is" in lines[0]


def test_process_scalar_list_fits():
    lines = []
    render.process_scalar_list(
        "conditions",
        lines,
        ["condition1", "condition2"],
    )
    assert lines == ["Conditions: condition1, condition2"]


def test_process_scalar_list_too_long():
    lines = []
    big_list = ["test_value" * 10, "another" * 5]
    render.process_scalar_list("giant_field", lines, big_list)
    assert lines[0].startswith("Giant Field:")
    assert lines[1].startswith("- test_value")


def test_render_key_value_short():
    lines = []
    render.render_key_value(lines, "nct_number", "nct100")
    assert lines == ["Nct Number: nct100"]


def test_render_key_value_long():
    lines = []
    render.render_key_value(lines, "brief_summary", "hello " * 15)
    # first line "brief summary:"
    assert lines[0] == "Brief Summary:"
    assert lines[1].startswith("  hello hello")
