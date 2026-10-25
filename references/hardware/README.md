[J501 AGX Orin](../../README.md) / [references](../) / **hardware**

# Connector meshes

Meshes of the carrier board's connectors, cut out of the vendor board model by [`tools/export_hardware.py`](../../tools/export_hardware.py).
They are used for the plate cutouts, the clearance checks and the renders.

Only [`indices.json`](indices.json), which maps each connector to its solids in the board model, is in the repository. The meshes are
rebuilt by `tools/fetch_references.py`. These are the renders of each one:

<table>
<tr>
<td width="25%" valign="top"><a href="../../preview/connector-front_power.png"><img src="../../preview/connector-front_power.png" alt="DC power input" width="100%"></a><br>DC power input</td>
<td width="25%" valign="top"><a href="../../preview/connector-ethernet_10g.png"><img src="../../preview/connector-ethernet_10g.png" alt="10G Ethernet" width="100%"></a><br>10G Ethernet</td>
<td width="25%" valign="top"><a href="../../preview/connector-ethernet_1g.png"><img src="../../preview/connector-ethernet_1g.png" alt="1G Ethernet" width="100%"></a><br>1G Ethernet</td>
<td width="25%" valign="top"><a href="../../preview/connector-rear_terminal.png"><img src="../../preview/connector-rear_terminal.png" alt="I/O terminal block" width="100%"></a><br>I/O terminal block</td>
</tr>
<tr>
<td width="25%" valign="top"><a href="../../preview/connector-rear_tall_connector.png"><img src="../../preview/connector-rear_tall_connector.png" alt="Rear tall connector" width="100%"></a><br>Rear tall connector</td>
<td width="25%" valign="top"><a href="../../preview/connector-rear_usb_lower.png"><img src="../../preview/connector-rear_usb_lower.png" alt="USB, lower" width="100%"></a><br>USB, lower</td>
<td width="25%" valign="top"><a href="../../preview/connector-rear_usb_upper.png"><img src="../../preview/connector-rear_usb_upper.png" alt="USB, upper" width="100%"></a><br>USB, upper</td>
<td width="25%" valign="top"><a href="../../preview/connector-rear_connector_flat.png"><img src="../../preview/connector-rear_connector_flat.png" alt="Rear flat connector" width="100%"></a><br>Rear flat connector</td>
</tr>
<tr>
<td width="25%" valign="top"><a href="../../preview/connector-rear_bottom_port_a.png"><img src="../../preview/connector-rear_bottom_port_a.png" alt="Rear bottom port A" width="100%"></a><br>Rear bottom port A</td>
<td width="25%" valign="top"><a href="../../preview/connector-rear_bottom_port_b.png"><img src="../../preview/connector-rear_bottom_port_b.png" alt="Rear bottom port B" width="100%"></a><br>Rear bottom port B</td>
<td width="25%" valign="top"><a href="../../preview/connector-front_bottom_port.png"><img src="../../preview/connector-front_bottom_port.png" alt="J18 nano-SIM" width="100%"></a><br>J18 nano-SIM</td>
<td width="25%" valign="top"><a href="../../preview/connector-side_header.png"><img src="../../preview/connector-side_header.png" alt="J17 side header" width="100%"></a><br>J17 side header</td>
</tr>
<tr>
<td width="25%" valign="top"><a href="../../preview/connector-module_socket.png"><img src="../../preview/connector-module_socket.png" alt="Module socket" width="100%"></a><br>Module socket</td>
<td width="25%"></td>
<td width="25%"></td>
<td width="25%"></td>
</tr>
</table>
