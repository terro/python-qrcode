=============================
Pure python QR Code generator
=============================

This module uses image libraries, Python Imaging Library (PIL) by default, to
generate QR Codes.

It is recommended to use the pillow_ fork rather than PIL itself.

.. _pillow: https://pypi.python.org/pypi/Pillow


What is a QR Code?
==================

A Quick Response code is a two-dimensional pictographic code used for its fast
readability and comparatively large storage capacity. The code consists of
black modules arranged in a square pattern on a white background. The
information encoded can be made up of any kind of data (e.g., binary,
alphanumeric, or Kanji symbols)

Usage
=====

In Python, use the ``make`` shortcut function::

    import qrcode
    img = qrcode.make('Some data here')

Advanced Usage
--------------

For more control, use the ``QRCode`` class. For example::

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        foreground="red",
        background="white",
        probe_in="blue",
        probe_out="green",
        style="water",
        logo=logo
    )
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image()

The ``version`` parameter is an integer from 1 to 40 that controls the size of
the QR Code (the smallest, version 1, is a 21x21 matrix).
Set to ``None`` and use the ``fit`` parameter when making the code to determine
this automatically.

The ``error_correction`` parameter controls the error correction used for the
QR Code. The following four constants are made available on the ``qrcode``
package:

``ERROR_CORRECT_L``
    About 7% or less errors can be corrected.
``ERROR_CORRECT_M`` (default)
    About 15% or less errors can be corrected.
``ERROR_CORRECT_Q``
    About 25% or less errors can be corrected.
``ERROR_CORRECT_H``.
    About 30% or less errors can be corrected.

The ``box_size`` parameter controls how many pixels each "box" of the QR code
is.

The ``border`` parameter controls how many boxes thick the border should be
(the default is 4, which is the minimum according to the specs).

The ``foreground``, ``background``, ``probe_in``, ``probe_out`` parameter controls the color of the QR code.

There are three ``style`` available: ``default`` (normal square block), ``round`` (circle block), ``water`` (liquid block).

You may also set a custom logo by passing a base64 encoded string to ``logo`` parameter. Note that use ``ERROR_CORRECT_H`` when you add a logo.