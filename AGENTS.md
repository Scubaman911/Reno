This is Reno - a release note templating tool.

TO DOs:
- Provide a toml config file where things like all the service names
can be populated (for now have services equal to: ServiceA, ServiceB and ServiceC)
- A Streamlit app called Reno, that has a DOCKERFILE so we can dockerise it easily
- A docker compose file that allows for easy orchestration of the Streamlit app

Key note:
Any functionality below should be dynamically built into a JSON object as the 
user edits the form. So the entire form in the background has a JSON representation.

The Reno app should consist of a form that lets the user:
- Pick a provisional date for the release
- Add a point of contact (these should be provided from config, for now have DevA, DevB pls)
- Add available services to the release note
Under an added service a user should be able to:
- toggle if the release is "Config only" or not
- There should be a dropdown for the risk level of the release Low, Medium, High
- A text box for a user to paste any links to PRs relevant to the service change.
- A text box for the user to paste any links to relevant designs for the change.
- A text box for the user to paste links to any applicable code quality reports
- A text box for any addition links, e.g. additional tests.

There should be 3 buttons at the bottom of the form
- Export to base64 (this should take the JSON representation of the form and encode it to base64)
- Load from base64 (takes the base64 string and populates the app form from it)
- Save to JPEG (saves a snapshot of the form to a JPEG image so a user can forward the notes to others.)