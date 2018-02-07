# Tagmon

Used for automatic expiration of tags that have been assigned by a configured log action on Panorama or firewall


## How it works

Tagmon is designed to be used in conjunction with automatic log actions (auto tagging). The feature was built to allow automatic tagging of either a source or destination (or both) IP address in logs that match the configured filter. The feature does not have an expiration function however. For use cases where addresses may need to have an automatic action applied to them for a limited time, Tagmon provides a mechanism for de-registering tags after an alloted time.

Tagmon listens on the configured port (8100 by default). When PAN-OS or Panorama forwards an IP address that has been tagged, Tagmon records the time. Once the allotted time has elapsed, Tagmon will send an API call to the firewall (or Panorama) to deregister the IP address from the tag (provided the address has not been seen again).

### Example Use Case
For threat logs related to DoS events, you can automatically tag the source address for use in a dynamic address group. In some cases, this condition may not be permanent (e.g. a misbehaving system is inadvertently causing the DoS). Tagmon will deregister the IP address after the allotted time, elimiating the need for personnel to manually make the change once the misbehaving system is fixed.

## Setup
1. Set the port: You can change the port that you want Tagmon to listen on by modifying the listener() function.
2. Configure an HTTP profile: Point the profile to the host that is running Tagmon. Configure the payload for any log type that you would like Tagmon to process.
    a. Protocol: HTTP
    b. Port: As configured in tagmon.py
    c. Payload: For each desired log type, configure the payload to contain "ip_is:$src" or "ip_is:$dst" depending on which
    address you are tagging in the log forwarding profile
3. Use the HTTP profile in the log forwarding profile of your choice

On startup, Tagmon will ask several questions including:
1. What the device IP address is
2. What the tag is
3. How long you would like to leave the object tagged

By default, Tagmon checks the timestamps for existing logs every hour (3600 seconds). This can be changed by modifying the while True: loop.

