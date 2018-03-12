#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2012-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski          #
#    (Laboratory of Neuroinformatics; Nencki Institute of Experimental        #
#    Biology of Polish Academy of Sciences)                                   #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################

"""
A collection of tools to access IntelliCage data.
"""
import sys

from ._Version import __version__, __RRID__, __ID__, __NeuroLexID__

from .LogAnalyser import (LickometerLogAnalyzer, PresenceLogAnalyzer,
                          FailureInspector, DataValidator, TestMiceData)
from ._GetTutorialData import getTutorialData
from ._ICData import Loader, Merger
from ._Metadata import Phase, ExperimentTimeline, Timeline
from ._Results import ResultsCSV
from ._Tools import hTime, convertTime, warn

from ._Bibliography import Citation

from . import (_dependencies, _Version, LogAnalyser, _GetTutorialData, _ICData,
               _Metadata, _Results, _Tools, _Bibliography)

# dependence tracking
import types
__dependencies__ = {m: (v, d)
                    for m, (v, d) in _dependencies.moduleDependencies(*[x for x in globals().values() if isinstance(x, types.ModuleType)]).items()
                    if (v is not None or d) and m not in ('pymice._Bibliography',
                                                          'pymice._Version',
                                                          're',
                                                          'csv')}

__all__ = []

__welcomeMessage = u"""PyMICE library v. {version}

The library is available under GPL3 license; we ask that reference to our paper
as well as to the library itself is provided in any published research making
use of PyMICE. Please run:

>>> print(pm.__REFERENCING__)

for more information (given that the library is imported as `pm`).


"""

__REFERENCING__ = u"""The recommended in-text citation format is:
{cite}

and the recommended bibliography entry format:
{cite.SOFTWARE}

{cite.PAPER}

If the journal does not allow for inclusion of the resource identifier
({rrid}) in the bibliography, we ask to provide it in-text:
{vancouver}

{vancouver.PAPER}
{vancouver.SOFTWARE}

We have provided a solution to facilitate referencing to the library. Please run

>>> help(pm.Citation)

for more information (given that the library is imported as `pm`).
""".format(rrid=__RRID__,
           cite=Citation(),
           vancouver=Citation(style='Vancouver'))

sys.stderr.write(__welcomeMessage.format(version=__version__,
                                         referencing=__REFERENCING__))

# COPYING, LICENSE and PGP key below
__COPYING__ = """PyMICE library v. {version}

Copyright (C) 2012-2017 Jakub M. Dzik a.k.a. Kowalski, S. Łęski
(Laboratory of Neuroinformatics; Nencki Institute of Experimental
Biology of Polish Academy of Sciences)

This software is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
   
This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this software.  If not, see http://www.gnu.org/licenses/.
""".format(version=__version__)
"Copyright information"

__LICENSE__ = """
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Use with the GNU Affero General Public License.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU Affero General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the special requirements of the GNU Affero General Public License,
section 13, concerning interaction through a network will apply to the
combination as such.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If the program does terminal interaction, make it output a short
notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, your program's commands
might be different; for a GUI interface, you would use an "about box".

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU GPL, see
<http://www.gnu.org/licenses/>.

  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<http://www.gnu.org/philosophy/why-not-lgpl.html>."""
"GPL v. 3"


__PGP_PUBLIC_KEY__ = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

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
LQFzmRxaKijtnb+pisAavRHkn85exT9m6w9j2w==
=rsm5
-----END PGP PUBLIC KEY BLOCK-----
"""
"PGP public key for verifying of package updates from PyPI"
