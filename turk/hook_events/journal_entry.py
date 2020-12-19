def set_name(je, method):
	naming_series = {"TURK": "TC-JV-"}
	name = naming_series.get(je.company) + je.name.split("-")[2]
	je.name = name
