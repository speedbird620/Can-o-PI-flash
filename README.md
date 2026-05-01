This module is intended to sit between a FLARM and a FLARM-display activating a canopy flasher depending on the information. It is a open source and open hardware project based on a Raspberry PI PICO and a MOSFET transistor. 

The blinker shall be deactivated with the folloing alogritm:
 - A FLARM is present in the NMEA-stream
 - The GPS-signal is valid
 - The GPS-unit is airborne
 - No glider within 1000 m hosrisontally and +-250 m vertically (values are configurable)
 - The program is executing

Please note that is any of the above conditions is not met, the blinker will be activated.

<img width="1279" height="905" alt="image" src="https://github.com/user-attachments/assets/1e9e232f-4c80-438c-b622-b64f98bf476e" />

<img width="1228" height="595" alt="image" src="https://github.com/user-attachments/assets/c8ba179a-5ed6-4617-8d6f-4a7e253b13a3" />

<img width="1311" height="678" alt="image" src="https://github.com/user-attachments/assets/75c3f354-8cba-4950-825b-ca93128ead18" />

To be continued
