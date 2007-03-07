======
Gracie
======

A simple OpenID provider for local system accounts
==================================================

:Author:    Ben Finney <ben+openid@benfinney.id.au>
:Updated:   2007-03-05

Gracie is an `OpenID`_ provider which authenticates users against
local Unix system accounts.

It is useful for projecting an existing Unix authentication system to
OpenID consumers.

..  _OpenID: http://openid.net/

Requirements
------------

* Python >= 2.4

* python-openid

* python-pam
  (for systems using PAM for authentication)

* Routes

PAM configuration
-----------------

For systems authenticating using PAM, you will need to define a PAM
configuration for the service `gracie` (for example, in the file
`/etc/pam.d/gracie`). This should have the following PAM
configuration::

    auth    required    pam_unix.so
    account required    pam_access.so

Copyright and License
---------------------

Gracie is copyright © 2007 Ben Finney <ben+python@benfinney.id.au>.

This is free software; you may copy, modify and/or distribute this
work under the terms of the `GNU General Public License`_, version 2
or, at your option, any later version of that license.
No warranty expressed or implied. See the file LICENSE for details.

..  _GNU General Public License: http://www.gnu.org/licenses/gpl.html
