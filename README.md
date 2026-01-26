# SwEng24-GuidewireHomeAlarm

## First Commits

- Avery
- Lance
- Matthew
- Thiago
- Kevin
- Veronika

## Proposed Framework

![image](Images\Framework_1.0.png)

### Notes:
- Open/Close Sensors can be put on windows as well. Also need to keep in mind scalability when introducing more sensors.
- ESP32 will send event states via wifi to our backend server. Backend code will then interpret events (ie. Open or close, which sensors etc)
- For frontend, we will have a web application for Maintenance/Admin and a mobile application for our end users.
- Finally, scalability needs to be kept in mind for multiple homes with multiple end users and ESP32. Also, good to keep in mind when developing that this security system can be easily integrated into a larger security system (Cameras, sensors etc).

## Proposed Tech Stack

| Layer | Tech | Description |
| :- | :-: | :- |
| Middleware (ESP32 Microcontroller) | ESPHome | Easy to implement API into our backend thats desgined for the ESP32 and can communicate with the device over wifi |
| Backend | Nodejs + MongoDB. Python / TypeScript | During Development, easiest to run backend locally. Not fully certain on deploying our backend but our best idea is using a rasberry pi as opposed to a cloud service. We will mostly use python / JavaScript as most of us are comfortable coding in those languages |
| Frontend | React / JavaScript. Koitlin + Gradle. | For admin/maintenance, we can use a simple web application using React and JavaScript. For end users, we can develop an android app using Kotilin (basically typeScript) and build with gradle. |

### Other Tech / Notes

- We can use google oauth to implement creating user accounts and keeping them secure. This will be in frontend and backend. It should be pretty simple then in one home to add user accounts with different roles (ie, owner, resident, maybe neighbour role?)
- We can use firebase for push notifications. This will be in frontend and backend.
- How we are gonna deploy our backend is what we still are kinda undecided on, but for now it's ok because it's easier to have local backend running during dev time.

