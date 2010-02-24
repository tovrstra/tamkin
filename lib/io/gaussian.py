# TAMkin is a post-processing toolkit for thermochemistry and kinetics analysis.
# Copyright (C) 2008-2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>,
# Matthias Vandichel <Matthias.Vandichel@UGent.be> and
# An Ghysels <An.Ghysels@UGent.be>, Center for Molecular Modeling (CMM), Ghent
# University, Ghent, Belgium; all rights reserved unless otherwise stated.
#
# This file is part of TAMkin.
#
# TAMkin is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# In addition to the regulations of the GNU General Public License,
# publications and communications based in parts on this program or on
# parts of this program are required to cite the following five articles:
#
# "Vibrational Modes in partially optimized molecular systems.", An Ghysels,
# Dimitri Van Neck, Veronique Van Speybroeck, Toon Verstraelen and Michel
# Waroquier, Journal of Chemical Physics, Vol. 126 (22): Art. No. 224102, 2007
# DOI:10.1063/1.2737444
#
# "Cartesian formulation of the Mobile Block Hesian Approach to vibrational
# analysis in partially optimized systems", An Ghysels, Dimitri Van Neck and
# Michel Waroquier, Journal of Chemical Physics, Vol. 127 (16), Art. No. 164108,
# 2007
# DOI:10.1063/1.2789429
#
# "Calculating reaction rates with partial Hessians: validation of the MBH
# approach", An Ghysels, Veronique Van Speybroeck, Toon Verstraelen, Dimitri Van
# Neck and Michel Waroquier, Journal of Chemical Theory and Computation, Vol. 4
# (4), 614-625, 2008
# DOI:10.1021/ct7002836
#
# "Mobile Block Hessian approach with linked blocks: an efficient approach for
# the calculation of frequencies in macromolecules", An Ghysels, Veronique Van
# Speybroeck, Ewald Pauwels, Dimitri Van Neck, Bernard R. Brooks and Michel
# Waroquier, Journal of Chemical Theory and Computation, Vol. 5 (5), 1203-1215,
# 2009
# DOI:10.1021/ct800489r
#
# "Normal modes for large molecules with arbitrary link constraints in the
# mobile block Hessian approach", An Ghysels, Dimitri Van Neck, Bernard R.
# Brooks, Veronique Van Speybroeck and Michel Waroquier, Journal of Chemical
# Physics, Vol. 130 (18), Art. No. 084107, 2009
# DOI:10.1063/1.3071261
#
# TAMkin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


from tamkin.data import Molecule, RotScan

from molmod.io import FCHKFile
from molmod import dihed_angle, amu, angstrom, lightspeed, centimeter

import numpy


__all__ = [
    "load_fixed_g03com", "load_molecule_g03fchk", "load_molecule_g98fchk",
    "load_rotscan_g03log", "make_moldenfile_nma",
]


def load_fixed_g03com(filename):
    f = file(filename)
    for line in f:
        # iterate until we reach the title line
        line = line.strip()
        if not (len(line)==0 or line[0] == "#" or line[0] == "%"):
            break
    for line in f:
        # skip lines until charge/multiplicty is reached
        words = line.split()
        if len(words) == 2:
            try:
                int(words[0])
                int(words[1])
                break
            except ValueError:
                pass
    counter = 0
    fixed_atoms = []
    for line in f:
        # go trough the list of atoms and store the fixed ones.
        words = line.split()
        if len(words) == 0:
            break
        if words[1] == "-1":
            fixed_atoms.append(counter)
        counter += 1
    return fixed_atoms


def load_molecule_g03fchk(fn_freq, fn_ener=None, fn_vdw=None, energy=None):
    """Load a molecule from Gaussian03 formatted checkpoint files

       Arguments:
         fn_freq  --  the formatted checkpoint file of the frequency job

       Optional arguments:
         fn_ener  --  the formatted checkpoint file of a single point
                      computation for the energy
         fn_vdw  --  An orca output file containing a Van der Waals correction
                     for the energy
         energy  --  override the energy from the formatted checkpoint file with
                     the given value
    """

    fchk_freq = FCHKFile(fn_freq, ignore_errors=True, field_labels=[
        "Cartesian Force Constants", "Real atomic weights", "Total Energy",
        "Multiplicity", "Cartesian Gradient"
    ])
    if fn_ener is None:
        fchk_ener = fchk_freq
    else:
        fchk_ener = FCHKFile(fn_ener, ignore_errors=True, field_labels=[
            "Total Energy"
        ])
    if energy is None:
        energy = fchk_ener.fields["Total Energy"]
    vdw = 0
    if fn_vdw is not None:
         f = file(fn_vdw)
         for line in f:
             if line.startswith("Van der Waals correction ="):
                 words = line.split()
                 vdw = float(words[5])
                 break
         f.close()

    return Molecule(
        fchk_freq.molecule.numbers,
        fchk_freq.molecule.coordinates,
        fchk_freq.fields["Real atomic weights"]*amu,
        energy+vdw,
        numpy.reshape(numpy.array(fchk_freq.fields["Cartesian Gradient"]), (len(fchk_freq.molecule.numbers),3)),
        fchk_freq.get_hessian(),
        fchk_freq.fields["Multiplicity"],
        None, # gaussian is very poor at computing the rotational symmetry number
        False,
    )


g98_masses = numpy.array([
    1.0079, 4.0026, 6.94, 9.01218, 10.81, 12.011, 14.0067, 15.9994, 18.9984,
    20.179, 22.98977, 24.305, 26.98154, 28.0855, 30.97376, 32.06, 35.453,
    39.948, 39.0983, 40.08, 44.9559, 47.9, 50.9415, 51.996, 54.938, 55.847,
    58.9332, 58.71, 63.546, 65.38, 69.735, 72.59, 74.9216, 78.96, 79.904, 83.8,
    85.4678, 87.62, 88.9059, 91.22, 92.9064, 95.94, 98.9062, 101.07, 102.9055,
    106.4, 107.868, 112.41, 114.82, 118.69, 121.75, 127.6, 126.9045, 131.3,
    132.9054, 137.33, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 178.49, 180.9479, 183.85, 186.207, 190.2, 192.22,
    195.09, 196.9665, 200.59, 204.37, 207.2, 208.9804, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0,
])*amu


def load_molecule_g98fchk(filename_freq, filename_ener=None):
    fchk_freq = FCHKFile(filename_freq, ignore_errors=True, field_labels=[
        "Cartesian Force Constants", "Total Energy",
        "Multiplicity", "Cartesian Gradient"
    ])
    if filename_ener is None:
        fchk_ener = fchk_freq
    else:
        fchk_ener = FCHKFile(filename_ener, ignore_errors=True, field_labels=[
            "Total Energy"
        ])
    masses = numpy.array([g98_masses[n-1] for n in fchk_freq.molecule.numbers])

    return Molecule(
        fchk_freq.molecule.numbers,
        fchk_freq.molecule.coordinates,
        masses,
        fchk_ener.fields["Total Energy"],
        numpy.reshape(numpy.array(fchk_freq.fields["Cartesian Gradient"]), (len(fchk_freq.molecule.numbers),3)),
        fchk_freq.get_hessian(),
        fchk_freq.fields["Multiplicity"],
        None, # gaussian is very poor at computing the rotational symmetry number
        False,
    )


def load_rotscan_g03log(fn_log, top_indexes=None):
    # find the line that specifies the dihedral angle
    f = file(fn_log)

    line = " "
    while len(line) > 0:
        line = f.readline()
        if line.startswith(" The following ModRedundant input section has been read:"):
            break
    if len(line) == 0:
        raise IOError("Could not find the ModRedundant section in the log file.")

    dihedral = None
    num_geoms = 0
    while len(line) > 0:
        line = f.readline()
        if len(line) < 2 or line[1] == ' ':
            break
        else:
            words = line.split()
            if words[0] == "D" and (words[5] == "S" or words[5] == "F"):
                if dihedral is None:
                    dihedral = tuple(int(word)-1 for word in words[1:5])
                else:
                    raise IOError("Found multiple dihedral angle scan, which is not supported.")

    if dihedral is None:
        raise IOError("Could not find the dihedral angle of the rotational scan.")

    # load all the energies and compute the corresponding angles
    energies = []
    angles = []
    geometries = []
    while len(line) > 0:
        line = f.readline()
        if line.startswith("                          Input orientation:"):
            # read the molecule
            numbers = []
            last_coordinates = []
            ## skip four lines
            f.readline()
            f.readline()
            f.readline()
            f.readline()
            line = f.readline()
            # read atoms
            while len(line) > 0 and not line.startswith(" -----"):
                words =  line.split()
                numbers.append(int(words[1]))
                last_coordinates.append((float(words[3]), float(words[4]), float(words[5])))
                line = f.readline()
        if line.startswith(" SCF Done:"):
            # read the energy
            last_energy = float(line[line.find("=")+1:].split()[0])
        if line.startswith("    -- Stationary point found."):
            # store last emergy and geometry in list
            energies.append(last_energy)
            last_coordinates = numpy.array(last_coordinates)*angstrom
            geometries.append(last_coordinates)
            angles.append(dihed_angle(
                last_coordinates[dihedral[0]], last_coordinates[dihedral[1]],
                last_coordinates[dihedral[2]], last_coordinates[dihedral[3]],
            )[0])

    if len(energies) == 0:
        raise IOError("Cold not find any stationary point")

    if top_indexes is None:
        # figure out what the two parts of the molecule are
        from molmod.molecules import Molecule as BaseMolecule
        molecule = BaseMolecule(numbers, geometries[0])
    else:
        molecule = None
    result = RotScan(
        dihedral, molecule, top_indexes,
        (numpy.array(angles), numpy.array(energies))
    )
    result.geometries = numpy.array(geometries)
    return result



#======================================
#    write logfile as Gaussian03 does
#======================================

# this file contains all texts needed to generate
# a .log file that can be read by molden (visualization program)
# - def make_molden_texts()
# - def make_moldenfile(filename, masses, atomicnumbers, positions, modes, ev)

def make_molden_texts():

   HEAD = """ Entering Gaussian System
 this file is generated from the MLDGAU subroutine in the file secder.F
 Please note, that this is a "faked" output;
 there are no intensities computed in CPMD."""

   head_coordinates = """ Standard orientation:
 ---------------------------------------------------------------------
Center     Atomic     Atomic              Coordinates (Angstroms)
Number     Number      Type              X           Y           Z
 ---------------------------------------------------------------------"""


   head_basisfunctions = """ ---------------------------------------------------------------------
       basis functions          primitive gaussians
       alpha electrons          beta electrons
 **********************************************************************"""

   head_end = " Normal termination of Gaussian 98."

   head_freq0= """ Harmonic frequencies (cm**-1), IR intensities (KM/Mole),
 Raman scattering activities (A**4/AMU), Raman depolarization ratios,
 reduced masses (AMU), force constants (mDyne/A) and normal coordinates:"""

   head_freq1_1 =  "                    ?A"
   head_freq1_2 =  "                    ?A                     ?A"
   head_freq1_3 =  "                    ?A                     ?A                     ?A"
   head_freq1 = [head_freq1_1,head_freq1_2,head_freq1_3]

   head_freq2 =  " Frequencies --"

   head_freq3_1 = """ Red. masses --     0.0000
 Frc consts  --     0.0000
 IR Inten    --     0.0000
 Raman Activ --     0.0000
 Depolar     --     0.0000
 Atom AN      X      Y      Z"""
   head_freq3_2 = """ Red. masses --     0.0000                 0.0000
 Frc consts  --     0.0000                 0.0000
 IR Inten    --     0.0000                 0.0000
 Raman Activ --     0.0000                 0.0000
 Depolar     --     0.0000                 0.0000
 Atom AN      X      Y      Z        X      Y      Z"""
   head_freq3_3 = """ Red. masses --     0.0000                 0.0000                 0.0000
 Frc consts  --     0.0000                 0.0000                 0.0000
 IR Inten    --     0.0000                 0.0000                 0.0000
 Raman Activ --     0.0000                 0.0000                 0.0000
 Depolar     --     0.0000                 0.0000                 0.0000
 Atom AN      X      Y      Z        X      Y      Z        X      Y      Z"""
   head_freq3 = [head_freq3_1,head_freq3_2,head_freq3_3]

   return HEAD, head_coordinates, head_basisfunctions, \
          head_freq0, head_freq1, head_freq2, head_freq3, head_end


def make_moldenfile_nma(filename, nma):
    """Write a logfile with the modes and frequencies
    in the way Gaussian03 does, such that molden can
    read this logfile.
    """
    if filename is None:
        filename = "molden.log"
    if nma.modes is None:
        raise ValueError("No modes available (do_modes=False), cannot write logfile with modes.")
    make_moldenfile(filename, nma.masses, nma.numbers, nma.coordinates,
                    nma.modes, nma.freqs )



def make_moldenfile(filename, masses, atomicnumbers, positions, modes, ev):
    """This function produces a molden-readable file: coordinates + frequencies + modes

    positions  -- coordinates, convert to angstrom
    modes  -- each col is a mode in mass weighted Cartesian coordinates
             un-mass-weighting necessary and renormalization (in order to see some movement)
    ev  -- eigenvalues (freqs), convert to cm-1
    """
    masses3_sqrt1 = numpy.array(sum([[1/m,1/m,1/m] for m in numpy.sqrt(masses)],[]))
    HEAD, head_coordinates, head_basisfunctions, \
    head_freq0, head_freq1, head_freq2, head_freq3, head_end = make_molden_texts()

    [rows,cols]=modes.shape
    number_of_atoms = rows/3
    number_of_modes = cols
    number_of_iterations = number_of_modes/3    # organisation of file: per 3 modes

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # start writing
    f = file(filename,"w+")

    print >> f, HEAD

    # ATOM PART
    print >> f, head_coordinates
    for at in range(number_of_atoms):
       print >> f, '%5d %10d %13s %15f %11f %11f' %(
                   at+1,atomicnumbers[at],"0",
                   positions[at,0]/angstrom,
                   positions[at,1]/angstrom,
                   positions[at,2]/angstrom)

    # ORBITAL PART
    print >> f, head_basisfunctions
    print >> f, " "   #this part is just empty

    # FREQUENCY PART
    print >> f, head_freq0

    for iteration in range(number_of_iterations):
        nb = 3*iteration   #number of mode
        mode1 = modes[:,nb]  *masses3_sqrt1
        mode2 = modes[:,nb+1]*masses3_sqrt1
        mode3 = modes[:,nb+2]*masses3_sqrt1
        mode1 = mode1/numpy.linalg.norm(mode1)
        mode2 = mode2/numpy.linalg.norm(mode2)
        mode3 = mode3/numpy.linalg.norm(mode3)
        print >> f, '%22d %22d %22d' %(nb+1,nb+2,nb+3)
        print >> f, head_freq1[2]
        print >> f, '%s %10.4f %22.4f %22.4f' %(head_freq2,
                                ev[nb]/lightspeed*centimeter,
                                ev[nb+1]/lightspeed*centimeter,
                                ev[nb+2]/lightspeed*centimeter)
        print >> f, head_freq3[2]
        for atomnb in range(number_of_atoms):
            i = 3*atomnb
            print >> f, '%4d %3d %8.2f %6.2f %6.2f %8.2f %6.2f %6.2f %8.2f %6.2f %6.2f' %(
                   atomnb+1 , atomicnumbers[atomnb],
                   mode1[i], mode1[i+1], mode1[i+2],
                   mode2[i], mode2[i+1], mode2[i+2],
                   mode3[i], mode3[i+1], mode3[i+2])

    rest = number_of_modes - 3*number_of_iterations

    if rest == 1:
        nb = number_of_modes-1   #number of mode: the last one
        mode1 = modes[:,nb]*masses3_sqrt1
        mode1 = mode1/numpy.linalg.norm(mode1)
        print >> f, '%22d' %(nb+1)
        print >> f, head_freq1[0]
        print >> f, '%s %10.4f' %(head_freq2, ev[nb]/lightspeed*centimeter)
        print >> f, head_freq3[0]
        for atomnb in range(number_of_atoms):
            i = 3*atomnb
            print >> f, '%4d %3d %8.2f %6.2f %6.2f' %(
                   atomnb+1 , atomicnumbers[atomnb],
                   mode1[i], mode1[i+1], mode1[i+2])

    elif rest == 2:
        nb = number_of_modes-2   #number of mode: the 2 last ones
        mode1 = modes[:,nb]  *masses3_sqrt1
        mode2 = modes[:,nb+1]*masses3_sqrt1
        mode1 = mode1/numpy.linalg.norm(mode1)
        mode2 = mode2/numpy.linalg.norm(mode2)
        print >> f, '%22d %22d' %(nb+1,nb+2)
        print >> f, head_freq1[1]
        print >> f, '%s %10.4f %22.4f' %(head_freq2,
                            ev[nb]  /lightspeed*centimeter,
                            ev[nb+1]/lightspeed*centimeter)
        print >> f, head_freq3[1]
        for atomnb in range(number_of_atoms):
            i = 3*atomnb
            print >> f, '%4d %3d %8.2f %6.2f %6.2f %8.2f %6.2f %6.2f' %(
                   atomnb+1 , atomicnumbers[atomnb],
                   mode1[i], mode1[i+1], mode1[i+2],
                   mode2[i], mode2[i+1], mode2[i+2],)

    elif rest != 0:
         print "error?! in number of iterations/number of atoms (writing molden file)"
    print >> f, head_end

    f.close()

#======================================
#    (END) write logfile as Gaussian03 does
#======================================
