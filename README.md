# soundcraft_ui16
This library is used by me to connect to the Soundcraft Ui16 using sockets.
The MixerBase class is used by MixerSender and MixerReceiver to manage shared functions and values.

MixerSender is a class to connect to the Mixer and send `SETD` commands to change all values on the mixer

MixerListener is a class to connect to the Mixer and listen to messages containing the `SETD` command formating them into a dict.
The message is then set into a queue given as arg on creation.

Splitting the Sender and Mixer helps to receive the messages for the options changed by the Sender. Running both in one connection wont yield the information send by this class.

Furthermore you might set values on one device and get/display information on another device.

# Examples
 * will be added later, when the full project is completed

# Soundcraft UI16 Mixer
[Manual](https://www.soundcraft.com/en/product_documents/ui_usermanual_v3-0-pdf-27c992b4-5132-4d2d-b8e2-79750de6ee29)

# Inspiration
[stefets/osc-soundcraft-bridge](https://github.com/stefets/osc-soundcraft-bridge/tree/main)
