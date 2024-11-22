# Install AppDaemon addon


# Add the following to the apps.yaml

```
wiring_central:
  module: wiring_central
  class: WiringCentral
```


# Correct the Timezone settings in appdaemon.yaml

```
---
secrets: /config/secrets.yaml
appdaemon:
  latitude: -35.307783
  longitude: 149.189049
  elevation: 2
  time_zone: Australia/Sydney
  plugins:
    HASS:
      type: hass
http:
  url: http://127.0.0.1:5050
admin:
api:
hadashboard:

```

Note: After making the timezone changes, the AppDaemon addon needs to be restarted.

#step:3
 - Copy wiring_central.py to apps folder.