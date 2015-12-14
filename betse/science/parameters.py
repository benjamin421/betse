#!/usr/bin/env python3
# Copyright 2014-2015 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

# Lodish H, Berk A, Zipursky SL, et al. Molecular Cell Biology. 4th edition. New York: W. H. Freeman;
# 2000. Section 15.4, Intracellular Ion Environment and Membrane Electric Potential.
# Available from: http://www.ncbi.nlm.nih.gov/books/NBK21627/

# FIXME create a planaria-specific (aquatic invertebrate) ion profile


from betse.exceptions import BetseExceptionParameters
from betse.science import simconfig
from betse.science.tissue.picker import (
    TissuePickerAll,
    TissuePickerBitmap,
    TissuePickerIndices,
    TissuePickerRandom,)
from betse.util.path import paths
from collections import OrderedDict
from matplotlib.colors import Colormap
import numpy as np
import matplotlib.cm as cm

# Parses the configuration file to define basic class holding all simulation variables
class Parameters(object):
    '''
    Storage for all user-defined parameters used in world-building,
    simulation, and plotting.

    These parameters are *deserialized* (i.e., read, loaded, and converted) from
    the user-defined YAML configuration file passed to this object on
    initialization.

    Attributes (General)
    ----------------------------
    config_dirname : str
        Absolute path of the directory containing the source YAML configuration
        file from which this object was first deserialized. This directory
        typically also contains example resources for use by BETSE's default
        configuration file (e.g., geometry-defining bitmaps).
    config_filename : str
        Absolute path of the source YAML configuration file from which this
        object was first deserialized.

    Attributes (General)
    ----------------------------
    clipping_bitmap_matcher : TissuePickerBitmap
        Object describing the bitmap whose colored pixel area specifies the
        global geometry mask to which all tissue profile bitmaps will be
        clipped.
    '''
    def __init__(self, config_filename: str):
        '''
        Parameters
        ----------------------------
        config_filename : str
            Absolute or relative path of the source YAML configuration file from
            which to deserialize this object.
        '''
        self._yamlConfigInit(config_filename)

    def _yamlConfigInit(self, config_filename: str):
        '''
        Parse parameters from the passed YAML configuration file.
        '''
        # Unique absolute path of the passed file and directory containing this
        # file. Since the latter uses the former, this dirname is guaranteed to
        # be non-empty and hence *NOT* raise an exception.
        self.config_filename = paths.canonicalize(config_filename)
        self.config_dirname = paths.get_dirname(self.config_filename)

        # Dictionary loaded from this YAML file.
        self.config = simconfig.load(self.config_filename)

        self.grid_size = int(self.config['general options']['comp grid size'])

        self.plot_grid_size = int(self.config['general options']['plot grid size'])

        self.sim_ECM = self.config['general options']['simulate extracellular spaces']    # boolean letting us know if extracellular spaces are included

        self.fluid_flow = self.config['world options']['fluid flow']['include fluid flow']

        self.sim_eosmosis = self.config['world options']['channel electroosmosis']['turn on']

        self.deformation = self.config['world options']['deformation']['turn on']

        self.td_deform = self.config['world options']['deformation']['time dependent']

        self.deform_osmo = self.config['variable settings']['flow and deformation']['include osmotic pressure']
        self.deform_electro = self.config['variable settings']['flow and deformation']['include electrostatic pressure']

        self.fixed_cluster_bound = self.config['variable settings']['flow and deformation']['fixed cluster boundary']


        self.youngMod = float(self.config['variable settings']['flow and deformation']['young modulus'])

        # calculate lame's parameters from young mod and the poisson ratio:
        self.poi = 0.45 # Poisson's ratio for the biological medium

        self.lame_mu = self.youngMod/(2*(1+self.poi))
        self.lame_lamb = (self.youngMod*self.poi)/((1+self.poi)*(1-2*self.poi))

        self.mu_membrane = 1.0 # membrane viscocity

        # in-membrane diffusion coefficient
        self.D_membrane = float(self.config['variable settings']['channel electroosmosis']['membrane mobility'])
        # charge of membrane pumps and channels:
        self.z_channel = float(self.config['variable settings']['channel electroosmosis']['channel charge'])

        self.z_pump = float(self.config['variable settings']['channel electroosmosis']['pump charge'])

        self.mu_water = float(self.config['variable settings']['flow and deformation']['water viscocity'])   # viscocity of water [Pa.s]

        self.mu_tissue = float(self.config['variable settings']['flow and deformation']['viscous damping']) # viscocity of tissue medium [Pa s}

        self.zeta = -70e-3  # zeta potential of cell membrane [V]

        self.gj_surface = float(self.config['variable settings']['gap junctions']['gap junction surface area'])

        self.gj_flux_sensitive = self.config['variable settings']['gap junctions']['gj flux sensitive']

        self.cavity_state = bool(self.config['variable settings']['cavity open'])

        # set time profile from yaml
        self.time_profile_init = self.config['init time settings']['time profile'] # time profile for initialization run
        self.time_profile_sim = self.config['sim time settings']['time profile']   # time profile for sim run

        self.time4init = self.config['init time settings']['total time']      # set the time for the initialization sim [s]
        self.time4sim = self.config['sim time settings']['total time']        # set total time for simulation [s]

        self.autoInit = self.config['automatically run initialization']

        # Define paths for saving initialization runs, simulation runs, and results:
        self.init_path = paths.join(
            self.config_dirname, self.config['init file saving']['directory'])  # world, inits, and sims are saved and read to/from this directory.
        self.sim_path = paths.join(
            self.config_dirname, self.config['sim file saving']['directory']) # folder to save unique simulation and data linked to init
        self.sim_results = paths.join(
            self.config_dirname, self.config['results file saving']['directory']) # folder to auto-save results (graphs, images, animations)

        self.init_filename = self.config['init file saving']['file']
        self.sim_filename = self.config['sim file saving']['file']
        self.world_filename = self.config['init file saving']['worldfile']

        self.backward_pumps = False   # boolean letting us know if pumps can run backwards

         # Geometric constants and factors
        self.wsx = float(self.config['world options']['world size'])  # the x-dimension of the world space
        self.wsy = self.wsx  # the y-dimension of the world space [m]
        self.rc = float(self.config['world options']['cell radius'])  # radius of single cell
        self.cell_height = float(self.config['world options']['cell height'])  # the height of a cell in the z-direction
        self.cell_space = float(self.config['world options']['cell spacing'])  # the true cell-cell spacing
        self.nl = float(self.config['world options']['lattice disorder'])  # noise level for the lattice

        volmult = 1

        self.vol_env = volmult*self.wsx*self.wsy*self.cell_height

        self.T = float(self.config['world options']['temperature'])  # Cells temperature

        self.gravity = self.config['variable settings']['flow and deformation']['gravity']

        self.aquaporins = float(self.config['variable settings']['flow and deformation']['membrane water conductivity'])

        self.gj_vthresh = float(self.config['variable settings']['gap junctions']['gj voltage threshold'])
        self.gj_vgrad  = float(self.config['variable settings']['gap junctions']['gj voltage window'])

        self.gj_respond_flow = False

        self.v_sensitive_gj = self.config['variable settings']['gap junctions']['voltage sensitive gj']

        self.env_type = True # for now, can't handle air boundaries

        self.D_tj = float(self.config['variable settings']['tight junction scaling'])

        self.D_adh = float(self.config['variable settings']['adherens junction scaling'])

        # tight junction relative ion movement properties:
        self.Dtj_rel = {}  # use a dictionary to hold the tj values:

        self.Dtj_rel['Na']=float(self.config['variable settings']['tight junction relative diffusion']['Na'])
        self.Dtj_rel['K']=float(self.config['variable settings']['tight junction relative diffusion']['K'])
        self.Dtj_rel['Cl']=float(self.config['variable settings']['tight junction relative diffusion']['Cl'])
        self.Dtj_rel['Ca']=float(self.config['variable settings']['tight junction relative diffusion']['Ca'])
        self.Dtj_rel['M']=float(self.config['variable settings']['tight junction relative diffusion']['M'])
        self.Dtj_rel['P']=float(self.config['variable settings']['tight junction relative diffusion']['P'])
        self.Dtj_rel['H']=float(self.config['variable settings']['tight junction relative diffusion']['H'])

        # default membrane diffusion constants: easy control of cell's base resting potential
        self.Dm_Na = float(self.config['variable settings']['default tissue properties']['Dm_Na'])     # sodium [m2/s]
        self.Dm_K = float(self.config['variable settings']['default tissue properties']['Dm_K'])     #  potassium [m2/s]
        self.Dm_Cl = float(self.config['variable settings']['default tissue properties']['Dm_Cl'])    # chloride [m2/s]
        self.Dm_Ca = float(self.config['variable settings']['default tissue properties']['Dm_Ca'])   #  calcium [m2/s]
        self.Dm_H = float(self.config['variable settings']['default tissue properties']['Dm_H'])    #  hydrogen [m2/s]
        self.Dm_M = float(self.config['variable settings']['default tissue properties']['Dm_M'])    #  anchor ion [m2/s]
        self.Dm_P = float(self.config['variable settings']['default tissue properties']['Dm_P'])     #  proteins [m2/s]

        # set ion profile to be used: 'basic' (4 ions), 'basic_Ca' (5 ions), 'animal' (7 ions), 'invertebrate' (7 ions)
        self.ion_profile = self.config['general options']['ion profile']

        # include full calcium dynamics in the situation (i.e. endoplasmic reticulum, etc)?
        self.Ca_dyn = self.config['Ca dynamics']['turn on']

        # include HK-ATPase in the simulation? Yes =1, No = 0
        self.HKATPase_dyn = self.config['variable settings']['optional pumps']['HKATPase pump']

        # include V-ATPase in the simulation? Yes =1, No = 0
        self.VATPase_dyn = self.config['variable settings']['optional pumps']['VATPase pump']

        # include diffusion of a morphogen (originally called a voltage-sensitive dye)?
        self.voltage_dye = self.config['variable settings']['morphogen properties']['include morphogen']

        self.Dm_Dye = float(self.config['variable settings']['morphogen properties']['Dm'])
        self.Do_Dye = float(self.config['variable settings']['morphogen properties']['Do'])
        self.z_Dye = float(self.config['variable settings']['morphogen properties']['z'])
        self.cDye_to = float(self.config['variable settings']['morphogen properties']['env conc'])
        self.cDye_to_cell = float(self.config['variable settings']['morphogen properties']['cell conc'])
        self.Dye_target_channel = self.config['variable settings']['morphogen properties']['ion channel target']
        self.Dye_Hill_K = float(self.config['variable settings']['morphogen properties']['target Hill coefficient'])
        self.Dye_Hill_exp = float(self.config['variable settings']['morphogen properties']['target Hill exponent'])
        self.Dye_peak_channel = float(self.config['variable settings']['morphogen properties']['peak channel opening'])
        self.Dye_acts_extracell = bool(self.config['variable settings']['morphogen properties']['acts extracellularly'])

        self.pump_Dye = bool(self.config['variable settings']['morphogen properties']['active pumping']['turn on'])
        self.pump_Dye_out = bool(self.config['variable settings']['morphogen properties']
                                ['active pumping']['pump to cell'])
        self.pump_Dye_alpha = float(self.config['variable settings']['morphogen properties']
                                ['active pumping']['maximum rate'])

        # include noise in the simulation?
        self.channel_noise_level = float(self.config['variable settings']['noise']['static noise level'])

        self.dynamic_noise = self.config['variable settings']['noise']['dynamic noise']
        self.dynamic_noise_level = float(self.config['variable settings']['noise']['dynamic noise level'])


        #---------------------------------------------------------------------------------------------------------------
        # Global Interventions
        #---------------------------------------------------------------------------------------------------------------

        # initialize dictionary keeping track of global scheduled options for the sim:
        self.global_options = {}

        bool_Naenv = bool(self.config['change Na env']['event happens'])
        bool_Kenv = bool(self.config['change K env']['event happens'])
        bool_Clenv = bool(self.config['change Cl env']['event happens'])
        bool_MorphEnv = bool(self.config['change morphogen']['event happens'])
        bool_gjblock = bool(self.config['block gap junctions']['event happens'])
        # bool_ecm = bool(self.config['change ecm junctions']['event happens'])
        bool_temp =  bool(self.config['change temperature']['event happens'])
        bool_NaKblock = bool(self.config['block NaKATP pump']['event happens'])
        bool_HKblock = bool(self.config['block HKATP pump']['event happens'])
        bool_Vblock = bool(self.config['block VATP pump']['event happens'])

        if bool_Kenv is False:
            self.global_options['K_env'] = 0
        elif bool_Kenv is True:
            on_Kenv = float(self.config['change K env']['change start'])
            off_Kenv = float(self.config['change K env']['change finish'])
            rate_Kenv = float(self.config['change K env']['change rate'])
            multi_Kenv = float(self.config['change K env']['multiplier'])
            kenv = [on_Kenv, off_Kenv, rate_Kenv, multi_Kenv]
            self.global_options['K_env'] = kenv

        if bool_Clenv is False:
            self.global_options['Cl_env'] = 0
        elif bool_Clenv is True:
            on_Clenv = float(self.config['change Cl env']['change start'])
            off_Clenv = float(self.config['change Cl env']['change finish'])
            rate_Clenv = float(self.config['change Cl env']['change rate'])
            multi_Clenv = float(self.config['change Cl env']['multiplier'])
            Clenv = [on_Clenv, off_Clenv, rate_Clenv, multi_Clenv]
            self.global_options['Cl_env'] = Clenv

        if bool_Naenv is False:
            self.global_options['Na_env'] = 0
        elif bool_Naenv is True:
            on_Naenv = float(self.config['change Na env']['change start'])
            off_Naenv = float(self.config['change Na env']['change finish'])
            rate_Naenv = float(self.config['change Na env']['change rate'])
            multi_Naenv = float(self.config['change Na env']['multiplier'])
            Naenv = [on_Naenv, off_Naenv, rate_Naenv, multi_Naenv]
            self.global_options['Na_env'] = Naenv

        if bool_MorphEnv is False:
            self.global_options['Morph_env'] = 0
        elif bool_MorphEnv is True:
            on_MorphEnv = float(self.config['change morphogen']['change start'])
            off_MorphEnv = float(self.config['change morphogen']['change finish'])
            rate_MorphEnv = float(self.config['change morphogen']['change rate'])
            conc_MorphEnv = float(self.config['change morphogen']['concentration'])
            MorphEnv = [on_MorphEnv, off_MorphEnv, rate_MorphEnv, conc_MorphEnv]
            self.global_options['Morph_env'] = MorphEnv

        if bool_gjblock is False:
            self.global_options['gj_block'] = 0
        elif bool_gjblock is True:
            on_gj = float(self.config['block gap junctions']['change start'])
            off_gj = float(self.config['block gap junctions']['change finish'])
            rate_gj = float(self.config['block gap junctions']['change rate'])
            fraction_gj = float(self.config['block gap junctions']['random fraction'])
            gjb = [on_gj,off_gj,rate_gj,fraction_gj]
            self.global_options['gj_block'] = gjb


        if bool_temp is False:
            self.global_options['T_change'] = 0
        elif bool_temp is True:
            on_T = float(self.config['change temperature']['change start'])
            off_T = float(self.config['change temperature']['change finish'])
            rate_T = float(self.config['change temperature']['change rate'])
            multi_T = float(self.config['change temperature']['multiplier'])
            temper = [on_T, off_T, rate_T, multi_T]
            self.global_options['T_change'] = temper

        if bool_NaKblock is False:
            self.global_options['NaKATP_block'] = 0
        elif bool_NaKblock is True:
            on_nak = float(self.config['block NaKATP pump']['change start'])
            off_nak = float(self.config['block NaKATP pump']['change finish'])
            rate_nak = float(self.config['block NaKATP pump']['change rate'])
            nak = [on_nak,off_nak,rate_nak]
            self.global_options['NaKATP_block'] = nak

        if bool_HKblock is False:
            self.global_options['HKATP_block'] = 0
        elif bool_HKblock is True:
            on_hk = float(self.config['block HKATP pump']['change start'])
            off_hk = float(self.config['block HKATP pump']['change finish'])
            rate_hk = float(self.config['block HKATP pump']['change rate'])
            hk = [on_hk,off_hk,rate_hk]
            self.global_options['HKATP_block'] = hk

        if bool_Vblock is False:
            self.global_options['VATP_block'] = 0
        elif bool_Vblock is True:
            on_v = float(self.config['block VATP pump']['change start'])
            off_v = float(self.config['block VATP pump']['change finish'])
            rate_v = float(self.config['block VATP pump']['change rate'])
            vk = [on_v,off_v,rate_v]
            self.global_options['VATP_block'] = vk

        #--------------------------------------------------------------------------------------------------------------
        # Tissue Definition
        #--------------------------------------------------------------------------------------------------------------
        # Import information used for defining tissues and boundary properties in the collective:
        tpd = self.config['tissue profile definition']
        self.default_tissue_name = \
            self.config['variable settings']['default tissue name']
        self.clipping_bitmap_matcher = TissuePickerBitmap(
            tpd['clipping']['bitmap']['file'], self.config_dirname)
        self.tissue_profiles = OrderedDict()
        self.boundary_profiles = OrderedDict()
        self.mem_labels = {'Dm_Na','Dm_K','Dm_Cl','Dm_Ca','Dm_H','Dm_M','Dm_P'}

        for i, tissue_profile in enumerate(tpd['tissue profiles']):
            profile_features = {}  # initialize a dictionary that will hold embeded data
            diffusion_constants = {}

            profile_name = tissue_profile['name']
            profile_features['designation'] = tissue_profile['designation']
            profile_features['insular gj'] = tissue_profile['insular']

            # Convert from 0-based list indices to 1-based z order.
            profile_features['z order'] = i + 1

            # Convert diffusion constants from strings to floats.
            for label in self.mem_labels:
                diffusion_constants[label] = float(tissue_profile[label])
            profile_features['diffusion constants'] = diffusion_constants

            # Convert this profile's matcher from a dictionary to typed object.
            profile_matcher = None
            cts = tissue_profile['cell targets']
            if cts['type'] == 'all':
                profile_matcher = TissuePickerAll()
            elif cts['type'] == 'bitmap':
                profile_matcher = TissuePickerBitmap(
                    cts['bitmap']['file'], self.config_dirname)
            elif cts['type'] == 'indices':
                profile_matcher = TissuePickerIndices(cts['indices'])
            elif cts['type'] == 'random':
                profile_matcher = TissuePickerRandom(cts['random'])
            else:
                raise BetseExceptionParameters(
                    'Tissue cell targets type "{}" unrecognized.'.format(
                        cts['type']))

            #FIXME: Rename "target method" to simply "matcher".
            profile_features['target method'] = profile_matcher

            # Finalize this tissue profile parameterization.
            self.tissue_profiles[profile_name] = profile_features

        for boundary_profile in tpd['boundary profiles']:
            profile_name_b = boundary_profile['name']
            profile_target_method_b = boundary_profile['boundary targets']
            self.boundary_profiles[profile_name_b] = profile_target_method_b

        # boundary properties:
        self.closed_bound = bool(tpd['closed boundary'])

        #---------------------------------------------------------------------------------------------------------------
        # Targeted Interventions
        #---------------------------------------------------------------------------------------------------------------
         # initialize dictionary keeping track of targeted scheduled options for the sim:
        self.scheduled_options = {}

        bool_Namem = bool(self.config['change Na mem']['event happens'])
        bool_Kmem = bool(self.config['change K mem']['event happens'])
        bool_Clmem = bool(self.config['change Cl mem']['event happens'])
        bool_Camem = bool(self.config['change Ca mem']['event happens'])
        bool_ip3 = bool(self.config['produce IP3']['event happens'])
        bool_extV = bool(self.config['apply external voltage']['event happens'])
        bool_ecmj = bool(self.config['break ecm junctions']['event happens'])
        bool_cut = bool(self.config['cutting event']['event happens'])

        if bool_Namem is False:
            self.scheduled_options['Na_mem'] = 0
        elif bool_Namem is True:
            on_Namem = float(self.config['change Na mem']['change start'])
            off_Namem = float(self.config['change Na mem']['change finish'])
            rate_Namem = float(self.config['change Na mem']['change rate'])
            multi_Namem = float(self.config['change Na mem']['multiplier'])
            apply_Namem = self.config['change Na mem']['apply to']
            function = self.config['change Na mem']['function']
            Namem = [on_Namem, off_Namem, rate_Namem, multi_Namem, apply_Namem,function]
            self.scheduled_options['Na_mem'] = Namem

        if bool_Kmem is False:
            self.scheduled_options['K_mem'] = 0
        elif bool_Kmem is True:
            on_Kmem = float(self.config['change K mem']['change start'])
            off_Kmem = float(self.config['change K mem']['change finish'])
            rate_Kmem = float(self.config['change K mem']['change rate'])
            multi_Kmem = float(self.config['change K mem']['multiplier'])
            apply_Kmem = self.config['change K mem']['apply to']
            function = self.config['change K mem']['function']
            Kmem = [on_Kmem, off_Kmem, rate_Kmem, multi_Kmem, apply_Kmem,function]
            self.scheduled_options['K_mem'] = Kmem

        if bool_Clmem is False:
            self.scheduled_options['Cl_mem'] = 0
        elif bool_Clmem is True:
            on_Clmem = float(self.config['change Cl mem']['change start'])
            off_Clmem = float(self.config['change Cl mem']['change finish'])
            rate_Clmem = float(self.config['change Cl mem']['change rate'])
            multi_Clmem = float(self.config['change Cl mem']['multiplier'])
            apply_Clmem = self.config['change Cl mem']['apply to']
            function = self.config['change Cl mem']['function']
            Clmem = [on_Clmem, off_Clmem, rate_Clmem, multi_Clmem, apply_Clmem, function]
            self.scheduled_options['Cl_mem'] = Clmem

        if bool_Camem is False:
            self.scheduled_options['Ca_mem'] = 0
        elif bool_Camem is True:
            on_Camem = float(self.config['change Ca mem']['change start'])
            off_Camem = float(self.config['change Ca mem']['change finish'])
            rate_Camem = float(self.config['change Ca mem']['change rate'])
            multi_Camem = float(self.config['change Ca mem']['multiplier'])
            apply_Camem = self.config['change Ca mem']['apply to']
            function = self.config['change Ca mem']['function']
            Camem = [on_Camem, off_Camem, rate_Camem, multi_Camem, apply_Camem,function]
            self.scheduled_options['Ca_mem'] = Camem

        if bool_ip3 is False:
            self.scheduled_options['IP3'] = 0
        elif bool_ip3 is True:
            on_ip3 = float(self.config['produce IP3']['change start'])
            off_ip3 = float(self.config['produce IP3']['change finish'])
            rate_ip3 = float(self.config['produce IP3']['change rate'])
            multi_ip3 = float(self.config['produce IP3']['multiplier'])
            apply_ip3 = self.config['produce IP3']['apply to']
            function = self.config['produce IP3']['function']
            ip3 = [on_ip3, off_ip3, rate_ip3, multi_ip3, apply_ip3,function]

            self.scheduled_options['IP3'] = ip3

        if bool_extV is False:
            self.scheduled_options['extV'] = 0
        elif bool_extV is True:
            on_extV = float(self.config['apply external voltage']['change start'])
            off_extV = float(self.config['apply external voltage']['change finish'])
            rate_extV = float(self.config['apply external voltage']['change rate'])
            peak_extV = float(self.config['apply external voltage']['peak value'])
            apply_extV = self.config['apply external voltage']['apply to']
            extV = [on_extV, off_extV, rate_extV, peak_extV, apply_extV]
            self.scheduled_options['extV'] = extV

        if bool_ecmj is False:
            self.scheduled_options['ecmJ'] = 0
        elif bool_ecmj is True:
            on_ecmj = float(self.config['break ecm junctions']['change start'])
            off_ecmj = float(self.config['break ecm junctions']['change finish'])
            rate_ecmj = float(self.config['break ecm junctions']['change rate'])
            apply_ecmj = self.config['break ecm junctions']['apply to']
            ecmj = [on_ecmj, off_ecmj, rate_ecmj, apply_ecmj]

            self.scheduled_options['ecmJ'] = ecmj


        if bool_cut is False:
            self.scheduled_options['cuts'] = 0

        else:
            cut_time = 0.0 # time event happens
            apply_to = self.config['cutting event']['apply to']    # tissue profile to apply this to
            dangling_gj = self.config['cutting event']['damaged membranes']  # does the cut produce env open cells?
            hurt_level = float(self.config['cutting event']['hurt level'])
            cuts_params = [cut_time, apply_to, dangling_gj,hurt_level]
            self.scheduled_options['cuts'] = cuts_params

        self.gradient_x_properties = {}
        self.gradient_y_properties = {}
        self.gradient_r_properties = {}

        self.gradient_x_properties['slope'] =self.config['function properties']['gradient_x']['slope']
        self.gradient_x_properties['offset'] =self.config['function properties']['gradient_x']['offset']

        self.gradient_y_properties['slope'] =self.config['function properties']['gradient_y']['slope']
        self.gradient_y_properties['offset'] =self.config['function properties']['gradient_y']['offset']

        self.gradient_r_properties['slope'] =self.config['function properties']['gradient_r']['slope']
        self.gradient_r_properties['offset'] =self.config['function properties']['gradient_r']['offset']


        #.........................DYNAMIC CHANNELS.....................................................................

        # cells to effect with voltage gated channels: (choices = 'none','all','random1','random50', [1,2,3])
        # self.gated_targets = self.config['ion channel target cells']

        bool_vgNa = bool(self.config['voltage gated Na+']['turn on'])
        bool_vgK = bool(self.config['voltage gated K+']['turn on'])
        bool_vgCa = bool(self.config['voltage gated Ca2+']['turn on'])
        bool_cagK = bool(self.config['calcium gated K+']['turn on'])

        # set specific character of gated ion channel dynamics:
        opNa = self.config['gated ion channel options']['voltage gated Na']
        opK = self.config['gated ion channel options']['voltage gated K']
        opCa = self.config['gated ion channel options']['voltage gated Ca']
        opcK = self.config['gated ion channel options']['calcium gated K']

        vgNa = [float(opNa['max Dmem Na']),float(opNa['activation v']),float(opNa['inactivation v']),float(opNa['deactivation v']),
            float(opNa['live time']),float(opNa['dead time'])]

        apply_vgNa = self.config['voltage gated Na+']['apply to']

        vgNa.append(apply_vgNa)

        vgK = [float(opK['max Dmem K']),float(opK['activation v']),float(opK['deactivation v']),float(opK['live time'])]

        apply_vgK = self.config['voltage gated K+']['apply to']

        vgK.append(apply_vgK)

        vgCa = [float(opCa['max Dmem Ca']),float(opCa['activation v']),float(opCa['inactivation v']),float(opCa['inactivation Ca']),
            float(opCa['reactivation Ca'])]

        apply_vgCa = self.config['voltage gated Ca2+']['apply to']

        vgCa.append(apply_vgCa)

        cagK = [float(opcK['max Dmem K']),float(opcK['hill K_half']),float(opcK['hill n'])]

        apply_cagK = self.config['calcium gated K+']['apply to']

        cagK.append(apply_cagK)

        # initialize dictionary holding options for dynamic channels:
        self.vg_options = {}

        if bool_vgNa is False:
            self.vg_options['Na_vg'] = 0
        elif bool_vgNa is True:
            self.vg_options['Na_vg'] = vgNa

        if bool_vgK is False:
            self.vg_options['K_vg'] = 0
        elif bool_vgK is True:
            self.vg_options['K_vg'] = vgK

        if bool_vgCa is False:
            self.vg_options['Ca_vg'] = 0
        elif bool_vgCa is True:
            self.vg_options['Ca_vg'] = vgCa

        if bool_cagK is False:
            self.vg_options['K_cag'] = 0
        elif bool_cagK is True:
            self.vg_options['K_cag'] = cagK

        # Calcium TissueHandler: Calcium Induced Calcium Release (CICR).....................................................

        cdp = self.config['calcium dynamics parameters']

        bool_CICR = bool(self.config['Ca dynamics']['turn on'])
        bool_calReg = bool(self.config['Ca dynamics']['include']['calcium regulation'])
        bool_frequMod = False  # FIXME temporarily disabled

        camid = float(cdp['CICR Ca peak'])
        cawidth = float(cdp['CICR Ca width'])

        self.Ca_dyn_options = {}

        if bool_CICR is False:

            self.Ca_dyn_options['CICR'] = 0

        elif bool_CICR is True:

            ERmax = float(cdp['ER max'])
            ERburst = float(cdp['ER burst'])
            ERclose = float(cdp['ER close'])

            ERstore_dyn = [ERmax,ERburst,ERclose]   # base dynamics of endoplasmic reticulum Ca2+ store.

            IP3_Khalf = float(cdp['IP3 K half'])
            IP3_hilln = float(cdp['IP3 hill n'])

            ip3_reg = [IP3_Khalf,IP3_hilln]   #  IP3 half-max, Hill coefficient

            if bool_calReg is False:
                ca_reg = []   # central concentration for Ca-act-Ca release [Ca mid, Ca width]
            elif bool_calReg is True:
                ca_reg = [camid, cawidth]

            if bool_frequMod is False:
                self.FMmod = 0              # frequency modulate ER response to IP3? 1 = yes, 0 = no
            elif bool_frequMod is True:
                self.FMmod = 1
                self.ip3FM = float(cdp['IP3 frequency modulation level'])

            apply_CICR = self.config['Ca dynamics']['apply to']

            cicr = [ERstore_dyn,ca_reg,ip3_reg,apply_CICR]
            self.Ca_dyn_options['CICR'] = cicr


        #........................RESULTS OUTPUT and PLOTTING............................................................

        # use the GHK equation to calculate alt Vmem from params?
        self.GHK_calc = self.config['variable settings']['use Goldman calculator']

        ro = self.config['results options']

        self.turn_all_plots_off = ro['turn all plots off']    # turn off all plots and animations for init and sim runs

        self.plot_cutlines = ro['plot cutlines']


         # Default colormap
        self.default_cm = get_colormap(ro['default colormap'])
           # options include cm.rainbow, cm.jet, cm.Blues, cm.Greens, see:
                                        # http://matplotlib.org/examples/color/colormaps_reference.html

        self.gj_cm = get_colormap(ro['gj colormap'])    # colormap for plotting gj currents on top of default colormap

        self.plot_while_solving = ro['plot while solving']  # create a 2d plot of cell vmems while solution is taking place

        self.save_solving_plot = ro['save solving plot']   # save the 2d plot generated while solving

        self.enumerate_cells = ro['enumerate cells']    # number cells on the static 2D maps

        self.plot_cell = ro['plot cell index']             # State the cell index to use for single-cell time plots

        self.plot_single_cell_graphs = ro['plot single cell graphs'] # plot graphs of concentration and voltage with t

        self.showCells = ro['show cells']     # True = polygon patch plots, False = trimesh

        self.I_overlay = ro['overlay currents']

        self.stream_density = ro['streamline density']

        self.IecmPlot = ro['plot total current']    # True = plot extracellular currents, false plot gj

        self.extVPlot = False   # plot the environmental spaces -- no longer used

        self.plotMask = ro['plot masked geometry']

        # options for individual 2D plots
        self.plot_vm2d = ro['Vmem 2D']['plot Vmem']                # 2d plot of final vmem ?
        self.autoscale_Vmem = ro['Vmem 2D']['autoscale colorbar']
        self.Vmem_min_clr = float(ro['Vmem 2D']['min val'])
        self.Vmem_max_clr = float(ro['Vmem 2D']['max val'])

        self.plot_ca2d = ro['Ca 2D']['plot Ca']                # 2d plot of final cell calcium ?
        self.autoscale_Ca = ro['Ca 2D']['autoscale colorbar']
        self.Ca_min_clr = float(ro['Ca 2D']['min val'])
        self.Ca_max_clr = float(ro['Ca 2D']['max val'])

        self.plot_ip32d = ro['IP3 2D']['plot IP3']               # 2d plot of final cIP3 ?
        self.autoscale_IP3 = ro['IP3 2D']['autoscale colorbar']
        self.IP3_min_clr = float(ro['IP3 2D']['min val'])
        self.IP3_max_clr = float(ro['IP3 2D']['max val'])

        self.plot_dye2d = ro['Morpho 2D']['plot Morpho']               # 2d plot of voltage sensitive dye in cell collective?
        self.autoscale_Dye = ro['Morpho 2D']['autoscale colorbar']
        self.Dye_min_clr = float(ro['Morpho 2D']['min val'])
        self.Dye_max_clr = float(ro['Morpho 2D']['max val'])

        self.plot_vcell2d = ro['Vcell 2D']['plot Vcell']
        self.autoscale_vcell = ro['Vcell 2D']['autoscale colorbar']
        self.vcell_min_clr = float(ro['Vcell 2D']['min val'])
        self.vcell_max_clr = float(ro['Vcell 2D']['max val'])

        self.plot_rho2d = ro['Charge 2D']['plot Charge']
        self.data_type_rho = ro['Charge 2D']['data type']
        self.autoscale_rho = ro['Charge 2D']['autoscale colorbar']
        self.rho_min_clr = float(ro['Charge 2D']['min val'])
        self.rho_max_clr = float(ro['Charge 2D']['max val'])

        self.plot_force2d = ro['Electrostatic 2D']['plot Electrostatic']
        self.autoscale_force = ro['Electrostatic 2D']['autoscale colorbar']
        self.force_min_clr = float(ro['Electrostatic 2D']['min val'])
        self.force_max_clr = float(ro['Electrostatic 2D']['max val'])

        self.plot_venv = ro['Venv 2D']['plot Venv']
        self.autoscale_venv = ro['Venv 2D']['autoscale colorbar']
        self.venv_min_clr = float(ro['Venv 2D']['min val'])
        self.venv_max_clr = float(ro['Venv 2D']['max val'])

        self.plot_I2d = ro['Currents 2D']['plot Currents']
        self.autoscale_I2d = ro['Currents 2D']['autoscale colorbar']
        self.I_min_clr = float(ro['Currents 2D']['min val'])
        self.I_max_clr = float(ro['Currents 2D']['max val'])

        self.plot_Efield = ro['Efield 2D']['plot Efield']   # 2d plot of electric field
        self.plot_Efield_type =ro['Efield 2D']['data type']   # data type can be 'ECM' or 'GJ'
        self.plot_Efield_vector =ro['Efield 2D']['overlay vector'] # overlay a streamline plot of field direction?
        self.autoscale_Efield =ro['Efield 2D']['autoscale colorbar'] # autoscale colorbar to min max of data set?
        self.Efield_min_clr =float(ro['Efield 2D']['max val'])         # maximum colorbar value in V/m
        self.Efield_max_clr =float(ro['Efield 2D']['min val'])       # maximum colorbar value in V/m

        self.plot_P = ro['Pressure 2D']['plot Pressure']
        self.autoscale_P = ro['Pressure 2D']['autoscale colorbar']
        self.P_min_clr = float(ro['Pressure 2D']['min val'])
        self.P_max_clr = float(ro['Pressure 2D']['max val'])

        self.plot_osmoP = ro['Osmotic Pressure 2D']['plot Osmotic Pressure']
        self.autoscale_osmoP = ro['Osmotic Pressure 2D']['autoscale colorbar']
        self.osmoP_min_clr = float(ro['Osmotic Pressure 2D']['min val'])
        self.osmoP_max_clr = float(ro['Osmotic Pressure 2D']['max val'])

        self.plot_Vel = ro['Velocity 2D']['plot Velocity']
        self.autoscale_Vel = ro['Velocity 2D']['autoscale colorbar']
        self.Vel_min_clr = float(ro['Velocity 2D']['min val'])
        self.Vel_max_clr = float(ro['Velocity 2D']['max val'])

        self.createAnimations = ro['create all animations']   # create all animations = True; turn off = False

        # specify desired animations:
        self.ani_vm2d = ro['Vmem Ani']['animate Vmem']                # 2d animation of vmem with time?
        self.autoscale_Vmem_ani = ro['Vmem Ani']['autoscale colorbar']
        self.Vmem_ani_min_clr = float(ro['Vmem Ani']['min val'])
        self.Vmem_ani_max_clr = float(ro['Vmem Ani']['max val'])

        self.ani_ca2d = ro['Ca Ani']['animate Ca2+']                # 2d animation of cell calcium with time ?
        self.autoscale_Ca_ani = ro['Ca Ani']['autoscale colorbar']
        self.Ca_ani_min_clr = float(ro['Ca Ani']['min val'])
        self.Ca_ani_max_clr = float(ro['Ca Ani']['max val'])

        self.ani_ip32d = ro['IP3 Ani']['animate IP3']               # 2d animation of cIP3 with time?
        self.autoscale_IP3_ani = ro['IP3 Ani']['autoscale colorbar']
        self.IP3_ani_min_clr = float(ro['IP3 Ani']['min val'])
        self.IP3_ani_max_clr = float(ro['IP3 Ani']['max val'])

        self.ani_dye2d = ro['Morpho Ani']['animate Morpho']               # 2d animation of voltage sensitive dye with time?
        self.autoscale_Dye_ani = ro['Morpho Ani']['autoscale colorbar']
        self.Dye_ani_min_clr = float(ro['Morpho Ani']['min val'])
        self.Dye_ani_max_clr = float(ro['Morpho Ani']['max val'])

        self.ani_vmgj2d = ro['Vmem GJ Ani']['animate Vmem with gj']     # 2d animation of vmem with superimposed gj network
        self.autoscale_Vgj_ani = ro['Vmem GJ Ani']['autoscale colorbar']
        self.Vgj_ani_min_clr = float(ro['Vmem GJ Ani']['min val'])
        self.Vgj_ani_max_clr = float(ro['Vmem GJ Ani']['max val'])

        self.ani_vcell = ro['Vcell Ani']['animate Vcell']
        self.autoscale_vcell_ani = ro['Vcell Ani']['autoscale colorbar']
        self.vcell_ani_min_clr = float(ro['Vcell Ani']['min val'])
        self.vcell_ani_max_clr = float(ro['Vcell Ani']['max val'])

        self.ani_venv = ro['Venv Ani']['animate Venv']
        self.autoscale_venv_ani = ro['Venv Ani']['autoscale colorbar']
        self.venv_ani_min_clr = float(ro['Venv Ani']['min val'])
        self.venv_ani_max_clr = float(ro['Venv Ani']['max val'])

        self.ani_Pcell = ro['P cell Ani']['animate P cell']
        self.autoscale_Pcell_ani = ro['P cell Ani']['autoscale colorbar']
        self.Pcell_ani_min_clr = float(ro['P cell Ani']['min val'])
        self.Pcell_ani_max_clr = float(ro['P cell Ani']['max val'])

        self.ani_osmoP = ro['Osmotic P Ani']['animate Osmotic P']
        self.autoscale_osmoP_ani = ro['Osmotic P Ani']['autoscale colorbar']
        self.osmoP_ani_min_clr = float(ro['Osmotic P Ani']['min val'])
        self.osmoP_ani_max_clr = float(ro['Osmotic P Ani']['max val'])

        self.ani_force = ro['Electrostatic P Ani']['animate electrostatic P']
        self.autoscale_force_ani = ro['Electrostatic P Ani']['autoscale colorbar']
        self.force_ani_min_clr = float(ro['Electrostatic P Ani']['min val'])
        self.force_ani_max_clr = float(ro['Electrostatic P Ani']['max val'])

        self.ani_I = ro['Current Ani']['animate current']
        self.autoscale_I_ani = ro['Current Ani']['autoscale colorbar']
        self.I_ani_min_clr = float(ro['Current Ani']['min val'])
        self.I_ani_max_clr = float(ro['Current Ani']['max val'])

        self.ani_mem = ro['Membrane Ani']['animate Membrane']
        self.autoscale_mem_ani = ro['Membrane Ani']['autoscale colorbar']
        self.mem_ani_min_clr = float(ro['Membrane Ani']['min val'])
        self.mem_ani_max_clr = float(ro['Membrane Ani']['max val'])

        self.ani_Efield = ro['Efield Ani']['animate Efield']   # 2d animation of electric field
        self.ani_Efield_type =ro['Efield Ani']['data type']   # data type can be 'ECM' or 'GJ'
        self.ani_Efield_vector =ro['Efield Ani']['overlay vector'] # overlay a streamline plot of field direction?
        self.autoscale_Efield_ani =ro['Efield Ani']['autoscale colorbar'] # autoscale colorbar to min max of data set?
        self.Efield_ani_min_clr =float(ro['Efield Ani']['max val'])         # maximum colorbar value in V/m
        self.Efield_ani_max_clr =float(ro['Efield Ani']['min val'])       # maximum colorbar value in V/m

        self.ani_Velocity = ro['Velocity Ani']['animate Velocity']   # 2d animation of electric field
        self.ani_Velocity_type =ro['Velocity Ani']['data type']   # data type can be 'ECM' or 'GJ'
        self.autoscale_Velocity_ani =ro['Velocity Ani']['autoscale colorbar'] # autoscale colorbar to min max of data set?
        self.Velocity_ani_min_clr =float(ro['Velocity Ani']['min val'])         # maximum colorbar value in V/m
        self.Velocity_ani_max_clr =float(ro['Velocity Ani']['max val'])       # maximum colorbar value in V/m

        self.ani_Deformation = ro['Deformation Ani']['animate Deformation']   # 2d animation of electric field
        self.ani_Deformation_type =ro['Deformation Ani']['data type']   # data type can be 'Vmem' or 'Displacement'
        self.autoscale_Deformation_ani =ro['Deformation Ani']['autoscale colorbar'] # autoscale colorbar to min max of data set?
        self.Deformation_ani_min_clr =float(ro['Deformation Ani']['min val'])         # maximum colorbar value in V/m
        self.Deformation_ani_max_clr =float(ro['Deformation Ani']['max val'])       # maximum colorbar value in V/m

        self.autosave = ro['automatically save plots']  # autosave all still images to a results directory
        self.saveAnimations = ro['save animations']    # save all animations as png sequences

        self.exportData = ro['export data to file']        # export all stored data for the plot_cell to a csv text file

        self.clip = 20e-6

        #........................INTERNAL USE ONLY.....................................................................

        # self.interp_type_2 ='tri'

        iu = self.config['internal parameters']

        self.interp_type = iu['interpolation method']

         # default free diffusion constants (cytoplasmic)
        self.Do_Na = float(iu['Do_Na'])      # free diffusion constant sodium [m2/s]
        self.Do_K = float(iu['Do_K'])      # free diffusion constant potassium [m2/s]
        self.Do_Cl = float(iu['Do_Cl'])     # free diffusion constant chloride [m2/s]
        self.Do_Ca = float(iu['Do_Ca'])     # free diffusion constant calcium [m2/s]
        self.Do_H = float(iu['Do_H'])      # free diffusion constant hydrogen [m2/s]
        self.Do_M = float(iu['Do_M'])     # free diffusion constant mystery anchor ion [m2/s]
        self.Do_P = float(iu['Do_P'])      # free diffusion constant protein [m2/s]

        # pump parameters
        self.alpha_NaK = float(iu['alpha_NaK']) # maximum rate constant sodium-potassium ATPase per unit surface area
        self.halfmax_NaK = float(iu['halfmax_NaK'])   # the free energy level at which pump activity is halved [kJ]
        self.slope_NaK = float(iu['slope_NaK'])  # the energy window width of the NaK-ATPase pump [kJ]

        self.alpha_Ca = float(iu['alpha_Ca']) # pump rate for calcium ATPase in membrane [1/mol*s] 2.0e-15
        self.alpha_CaER = float(iu['alpha_CaER'])  # pump rate for calcium ATPase in endoplasmic reticulum
        self.halfmax_Ca = float(iu['halfmax_Ca'])
        self.slope_Ca = float(iu['slope_Ca'])

        self.alpha_HK = float(iu['alpha_HK'])  # pump rate for the H-K-ATPase per unit surface area [1/mol*s] range 5.oe-4 to 2.5e-3
        self.halfmax_HK = float(iu['halfmax_HK'])
        self.slope_HK = float(iu['slope_HK'])

        self.alpha_V = float(iu['alpha_V'])  # pump rate for the V-ATPase per unit surface area [1/mol*s] range 5.oe-4 to 2.5e-3
        self.halfmax_V = float(iu['halfmax_V'])
        self.slope_V = float(iu['slope_V'])

        self.max_gj_enhancement = float(iu['max_gj_enhancement'])   # parameters relating to flow sensitivity of gap junctions
        self.u_decay_rate = float(iu['u_decay_rate'])
        self.alpha_rho_gj = float(iu['alpha_rho_gj'])

         # Calcium dynamics parameters
        self.ER_vol = float(cdp['ER_vol'])   # volume of endoplasmic reticulum as a fraction of cell volume
        self.ER_sa = float(cdp['ER_sa'])     # surface area of endoplasmic reticulum as a fraction of cell surface area

        self.Dm_IP3 = float(cdp['Dm_IP3'])   # membrane diffusion constant of IP3
        self.Do_IP3 = float(cdp['Do_IP3'])    # IP3 free diffusion constant [m2/s]
        self.z_IP3 = float(cdp['z_IP3'])        # charge valence of IP3
        self.cIP3_to = float(cdp['cIP3_to'])     # initial value of IP3 in all cells
        self.cIP3_to_env = float(cdp['cIP3_to_env'])  # initial value of IP3 in environment

        self.ff_env = float(iu['env modification constant'])
        self.ff_cell = float(iu['cell modification constant'])

        # partial pressure dissolved CO2
        self.CO2 = 40.0   # [mmHg]

        # charge states of ions
        self.z_Na = 1
        self.z_K = 1
        self.z_Cl = -1
        self.z_Ca = 2
        self.z_H = 1
        self.z_P = -1
        self.z_M = -1

        # molar mass of ions (kg/mol):
        self.M_Na = 23e-3
        self.M_K = 39e-3
        self.M_Cl = 35e-3
        self.M_Ca = 40e-3
        self.M_H = 1e-3
        self.M_P = 500e-3
        self.M_M = 60e-3

        # fundamental constants
        self.F = 96485 # Faraday constant [J/V*mol]
        self.R = 8.314  # Gas constant [J/K*mol]
        self.eo = 8.854e-12 # permittivity of free space [F/m]
        self.kb = 1.3806e-23  # Boltzmann constant [m2 kg/ s2 K1]
        self.q = 1.602e-19    # electron charge [C]
        self.mu = 1.275e-6   # magnetic permeability [H/m or N/A2]

        self.deltaGATP = 20*self.R*self.T    # free energy released in ATP hydrolysis [J/mol]

        self.ac = 1.0e-6  # cell-cell separation for drawing
        self.scale_cell = 0.90          # the amount to scale cell membranes in from ecm edges (only affects drawing)
        self.cm = 0.022            # patch capacitance of cell membrane up to 0.022 [F/m2]
        self.tm = 7.5e-9           # thickness of cell membrane [m]
        self.cell_sides = 4      # minimum number of membrane domains per cell (must be >2)
        self.scale_alpha = 1.4   # the amount to scale (1/d_cell) when calculating the concave hull (boundary search)
        self.merge_cut_off = (1/50)  # the fraction of nominal cell perimeter at which nearby ecm points are merged

        self.d_cell = self.rc * 2  # diameter of single cell
        self.nx = int(self.wsx / self.d_cell)  # number of lattice sites in world x index
        self.ny = int(self.wsy / self.d_cell)  # number of lattice sites in world y index
        self.wsx = self.wsx + 5 * self.nl * self.d_cell  # readjust the world size for noise
        self.wsy = self.wsy + 5 * self.nl * self.d_cell

        self.gjl = 2*self.tm + self.cell_space     # gap junction length
        self.gj_radius = 1.0e-9              # effective radius of gap junctions connecting cells [m] (range 0 to 5.0 e-9 m)

        self.um = 1e6    # multiplication factor to convert m to um

        self.self_cap_cell = (8 + 4.1*((self.cell_height/self.rc)**0.76))*self.eo*80*self.rc

        self.isamples = 40.0  # sampling of vector data for currents

        self.mem_const = (80.0*self.eo/self.mu_membrane)*self.zeta    # electroosmosis constant

        self.water_const = (80.0*self.eo/self.mu_water)*self.zeta    # electroosmosis constant

        self.rho = 1000 # mass density of system [kg/m3]

        # simplest ion ion_profile giving realistic results with minimal ions (Na+ & K+ focus):
        if self.ion_profile == 'basic':

            self.cNa_env = 145.0
            self.cK_env = 5.0
            self.cP_env = 10.0

            zs = [self.z_Na, self.z_K, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            assert self.z_M_env == -1

            self.cNa_cell = 7.8
            self.cK_cell = 146.5
            self.cP_cell = 138.0

            conc_cell = [self.cNa_cell,self.cK_cell, self.cP_cell]

            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            assert self.z_M_cell == -1

            self.ions_dict = {'Na':1,'K':1,'Cl':0,'Ca':0,'H':0,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'P':self.z_P,'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'P':self.Do_P,'M':self.Do_M}
            self.molar_mass = {'Na':self.M_Na,'K':self.M_K,'P':self.M_P,'M':self.M_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','P':'proteins','M':'anion'}



        elif self.ion_profile == 'basic_Ca':

            self.cNa_env = 145.0
            self.cK_env = 5.0
            self.cCa_env = 1.0
            self.cP_env = 10.0

            zs = [self.z_Na, self.z_K, self.z_Ca, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cCa_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            assert self.z_M_env == -1

            self.cNa_cell = 7.8
            self.cK_cell = 146.5
            self.cCa_cell = 1.0e-3
            self.cP_cell = 138.0

            conc_cell = [self.cNa_cell,self.cK_cell, self.cCa_cell, self.cP_cell]

            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            assert self.z_M_cell == -1

            self.cCa_er = 1.0e-3
            self.cM_er = self.cCa_er

            self.ions_dict = {'Na':1,'K':1,'Cl':0,'Ca':1,'H':0,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'Ca':self.cCa_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'Ca':self.cCa_env,'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'Ca':self.Dm_Ca, 'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'Ca':self.z_Ca, 'P':self.z_P,'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'Ca':self.Do_Ca, 'P':self.Do_P,'M':self.Do_M}
            self.molar_mass = {'Na':self.M_Na,'K':self.M_K,'Ca':self.M_Ca, 'P':self.M_P,'M':self.M_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','Ca':'calcium','P':'proteins','M':'anion'}

        # default environmental and cytoplasmic initial values mammalian cells
        elif self.ion_profile == 'animal':

            self.cNa_env = 145.0
            self.cK_env = 5.0
            self.cCl_env = 105.0
            self.cCa_env = 1.0
            self.cH_env = 6.98e-8
            self.cP_env = 10.0

            zs = [self.z_Na, self.z_K, self.z_Cl, self.z_Ca, self.z_H, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cCa_env, self.cH_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            assert self.z_M_env == -1

            self.cNa_cell = 7.8
            self.cK_cell = 146.5
            self.cCl_cell = 15.0
            self.cCa_cell = 1.0e-3
            self.cH_cell = 6.31e-8
            self.cP_cell = 138.0

            conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell, self.cCa_cell, self.cH_cell, self.cP_cell]
            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            assert self.z_M_cell == -1

            self.cCa_er = 0.5
            self.cM_er = - self.cCa_er

            self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':1,'H':1,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'Ca':self.cCa_cell,'Cl':self.cCl_cell,'H':self.cH_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'Ca':self.cCa_env,'Cl':self.cCl_env,'H':self.cH_env,'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'Ca':self.Dm_Ca,'Cl':self.Dm_Cl,'H':self.Dm_H,'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'Ca':self.z_Ca,'Cl':self.z_Cl,'H':self.z_H,'P':self.z_P,'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'Ca':self.Do_Ca,'Cl':self.Do_Cl,'H':self.Do_Cl,'P':self.Do_P,'M':self.Do_M}
            self.molar_mass = {'Na':self.M_Na,'K':self.M_K,'Ca':self.M_Ca,'Cl':self.M_Cl,'H':self.M_Cl,'P':self.M_P,'M':self.M_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','Ca':'calcium','Cl':'chloride','H':'protons','P':'proteins','M':'anion'}

         # default environmental and cytoplasm values invertebrate cells
        elif self.ion_profile == 'invertebrate':
            # self.cNa_env = 440.0
            # self.cK_env = 20.0
            # self.cCl_env = 460.0
            # self.cCa_env = 10.0
            # self.cH_env = 3.98e-5
            # self.cP_env = 7.0

            self.cNa_env = 8.7
            self.cK_env = 0.31
            self.cCl_env = 5.64
            self.cCa_env = 3.75
            self.cH_env = 3.98e-8
            self.cP_env = 7.0

            zs = [self.z_Na, self.z_K, self.z_Cl, self.z_Ca, self.z_H, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cCa_env, self.cH_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            assert self.z_M_env == -1

            # self.cNa_cell = 8.66
            # self.cK_cell = 406.09
            # self.cCl_cell = 45.56
            # self.cCa_cell = 3.0e-4
            # self.cH_cell = 6.31e-5
            # self.cP_cell = 350.0

            self.cNa_cell = 5.00
            self.cK_cell = 406.09
            self.cCl_cell = 45.56
            self.cCa_cell = 3.0e-4
            self.cH_cell = 6.31e-8
            self.cP_cell = 350.0

            conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell, self.cCa_cell, self.cH_cell, self.cP_cell]

            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            assert self.z_M_cell == -1

            self.cCa_er = 0.5
            self.cM_er = -self.cCa_er

            self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':1,'H':1,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'Ca':self.cCa_cell,'Cl':self.cCl_cell,'H':self.cH_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'Ca':self.cCa_env,'Cl':self.cCl_env,'H':self.cH_env,'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'Ca':self.Dm_Ca,'Cl':self.Dm_Cl,'H':self.Dm_H,'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'Ca':self.z_Ca,'Cl':self.z_Cl,'H':self.z_H,'P':self.z_P,'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'Ca':self.Do_Ca,'Cl':self.Do_Cl,'H':self.Do_H,'P':self.Do_P,'M':self.Do_M}
            self.molar_mass= {'Na':self.M_Na,'K':self.M_K,'Ca':self.M_Ca,'Cl':self.M_Cl,'H':self.M_H,'P':self.M_P,'M':self.M_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','Ca':'calcium','Cl':'chloride','H':'protons','P':'proteins','M':'anion'}

        elif self.ion_profile == 'scratch':

            self.cNa_env = 145.0
            self.cK_env = 5.0
            self.cCl_env = 105.0
            self.cP_env = 10.0

            zs = [self.z_Na, self.z_K, self.z_Cl, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            assert self.z_M_env == -1

            self.cNa_cell = 145.0
            self.cCl_cell = 80.0
            self.cK_cell = 85.0
            self.cP_cell = 138.0

            conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell,self.cP_cell]

            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            assert self.z_M_cell == -1

            self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':0,'H':0,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'Cl':self.cCl_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'Cl':self.cCl_env,'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'Cl':self.Dm_Cl ,'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'Cl':self.z_Cl,'P':self.z_P,'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'Cl':self.Do_Cl,'P':self.Do_P,'M':self.Do_M}
            self.molar_mass = {'Na':self.M_Na,'K':self.M_K,'Cl':self.M_Cl,'P':self.M_P,'M':self.M_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','Cl':'chloride','P':'proteins','M':'anion'}

        # user-specified environmental and cytoplasm values (customized)
        elif self.ion_profile == 'customized':

            self.cCa_er = 0.5
            self.cM_er = -self.cCa_er

            cip = self.config['general options']['customized ion profile']

            self.cNa_env = float(cip['extracellular Na+ concentration'])
            self.cK_env = float(cip['extracellular K+ concentration'])
            self.cCl_env = float(cip['extracellular Cl- concentration'])
            self.cCa_env = float(cip['extracellular Ca2+ concentration'])
            self.cH_env = float(cip['extracellular H+ concentration'])
            self.cP_env = float(cip['extracellular protein- concentration'])

            self.cNa_cell = float(cip['cytosolic Na+ concentration'])
            self.cK_cell = float(cip['cytosolic K+ concentration'])
            self.cCl_cell = float(cip['cytosolic Cl- concentration'])
            self.cCa_cell = float(cip['cytosolic Ca2+ concentration'])
            self.cH_cell = float(cip['cytosolic H+ concentration'])
            self.cP_cell = float(cip['cytosolic protein- concentration'])

            zs = [self.z_Na, self.z_K, self.z_Cl, self.z_Ca, self.z_H, self.z_P]

            conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cCa_env, self.cH_env, self.cP_env]
            self.cM_env, self.z_M_env = bal_charge(conc_env,zs)

            if self.z_M_env == 1:
                raise BetseExceptionParameters("You have defined a net negative charge profile in the environment: "
                                               "it cannot be charge balanced by an anion. Please try again.")


            conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell, self.cCa_cell, self.cH_cell, self.cP_cell]
            self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)

            if self.z_M_cell == 1:
                raise BetseExceptionParameters("You have defined a net negative charge profile in the cell: "
                                               "it cannot be charge balanced by an anion. Please try again.")

            self.cCa_er = float(cip['endoplasmic reticulum Ca2+'])
            self.cM_er = -self.cCa_er

            self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':1,'H':1,'P':1,'M':1}
            self.cell_concs ={'Na':self.cNa_cell,'K':self.cK_cell,'Ca':self.cCa_cell,'Cl':self.cCl_cell,
                'H':self.cH_cell,'P':self.cP_cell,'M':self.cM_cell}
            self.env_concs ={'Na':self.cNa_env,'K':self.cK_env,'Ca':self.cCa_env,'Cl':self.cCl_env,'H':self.cH_env,
                'P':self.cP_env,'M':self.cM_env}
            self.mem_perms = {'Na':self.Dm_Na,'K':self.Dm_K,'Ca':self.Dm_Ca,'Cl':self.Dm_Cl,'H':self.Dm_H,
                'P':self.Dm_P,'M':self.Dm_M}
            self.ion_charge = {'Na':self.z_Na,'K':self.z_K,'Ca':self.z_Ca,'Cl':self.z_Cl,'H':self.z_H,'P':self.z_P,
                'M':self.z_M}
            self.free_diff = {'Na':self.Do_Na,'K':self.Do_K,'Ca':self.Do_Ca,'Cl':self.Do_Cl,'H':self.Do_H,
                'P':self.Do_P,'M':self.Do_M}
            self.molar_mass = {'Na':self.M_Na,'K':self.M_K,'Ca':self.M_Ca,'Cl':self.M_Cl,'H':self.M_H,
                'P':self.Do_P,'M':self.Do_M}
            self.ion_long_name = {'Na':'sodium','K':'potassium','Ca':'calcium','Cl':'chloride','H':'protons',
                'P':'proteins','M':'anion'}

        else:

            raise BetseExceptionParameters("Oops! Looks like you've supplied an unavailable name for the ion profile "
                                               "under General Options of the config file. Please try again.")


    def set_time_profile(self,time_profile):

        if time_profile == 'simulate somatic':

            if self.sim_ECM is False:

                self.dt = 1e-3    # Simulation step-size [s] recommended range 5e-3 to 1e-4 for regular sims; 5e-5 for neural
                self.sim_end = self.time4sim         # world time to end the simulation
                self.resamp = 0.1         # time to resample in world time

                self.sim_tsteps = self.sim_end/self.dt    # Number of timesteps for the simulation
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.


            elif self.sim_ECM is True:

                self.dt = 1.0e-3    # Simulation step-size [s] recommended range 5e-3 to 1e-4 for regular sims; 5e-5 for neural
                self.sim_end = self.time4sim         # world time to end the simulation
                self.resamp = 0.1         # time to resample in world time

                self.sim_tsteps = self.sim_end/self.dt    # Number of timesteps for the simulation
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.

                # self.gjsa = math.pi*((self.gj_radius)**2)      # total gap junction surface area as fraction of cell surface area

        elif time_profile == 'simulate excitable':

            if self.sim_ECM is False:

                self.dt = 1.0e-4    # Simulation step-size [bs] recommended range 5e-3 to 1e-4 for regular sims; 2.5e-5 for neural
                self.sim_end = self.time4sim         # world time to end the simulation
                self.resamp = 5e-4         # time to resample in world time

                self.sim_tsteps = self.sim_end/self.dt    # Number of timesteps for the simulation
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.

                # self.gj_radius = 1.0e-8              # effective radius of gap junctions connecting cells [m] (range 0 to 5.0 e-9 m)
                # self.gjsa = math.pi*((self.gj_radius)**2)      # total gap junction surface area as fraction of cell surface area

            elif self.sim_ECM is True:

                self.dt = 1.0e-4    # Simulation step-size [bs] recommended range 5e-3 to 1e-4 for regular sims; 2.5e-5 for neural
                self.sim_end = self.time4sim         # world time to end the simulation
                self.resamp = 5e-4         # time to resample in world time

                self.sim_tsteps = self.sim_end/self.dt    # Number of timesteps for the simulation
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.

                # self.gj_radius = 1.0e-8              # effective radius of gap junctions connecting cells [m] (range 0 to 5.0 e-9 m)
                # self.gjsa = math.pi*((self.gj_radius)**2)      # total gap junction surface area as fraction of cell surface area


        elif time_profile == 'initialize':

            if self.sim_ECM is False:

                self.dt = 5.0e-3    # Simulation step-size [s] recommended range 1e-2 to 1e-3 for regular sims; 5e-5 for neural
                self.init_end = self.time4init      # world time to end the initialization simulation time [s]
                self.resamp = 0.1         # time to resample in world time

                self.init_tsteps = self.init_end/self.dt # Number of timesteps for an initialization from scratch (range 50000 to 100000)
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.

                # self.gj_radius = 1.0e-9              # effective radius of gap junctions connecting cells [m] (range 0 to 5.0 e-9 m)
                # self.gjsa = math.pi*((self.gj_radius)**2)      # total gap junction surface area as fraction of cell surface area

            elif self.sim_ECM is True:

                self.dt = 1.0e-3    # Simulation step-size [s] recommended range 1e-2 to 1e-3 for regular sims; 5e-5 for neural
                self.init_end = self.time4init      # world time to end the initialization simulation time [s]
                self.resamp = 0.1         # time to resample in world time

                self.init_tsteps = self.init_end/self.dt # Number of timesteps for an initialization from scratch (range 50000 to 100000)
                self.t_resample = self.resamp/self.dt         # resample the time vector every x steps
                self.method = 0            # Solution method. For 'Euler' = 0, for 'RK4' = 1.

                # self.gj_radius = 1.0e-9              # effective radius of gap junctions connecting cells [m] (range 0 to 5.0 e-9 m)
                # self.gjsa = math.pi*((self.gj_radius)**2)      # total gap junction surface area as fraction of cell surface area

        elif time_profile == 'custom init':

            self.dt = float(self.config['init time settings']['custom init time profile']['time step'])
            self.init_end = float(self.config['init time settings']['custom init time profile']['total time'])
            self.init_tsteps = self.init_end/self.dt
            self.resample = float(self.config['init time settings']['custom init time profile']['sampling rate'])
            self.t_resample = self.resample/self.dt
            self.method = 0
            # self.gj_radius = float(self.config['init time settings']['custom init time profile']['gap junction radius'])
            # self.gjsa = math.pi*((self.gj_radius)**2)

        elif time_profile == 'custom sim':

            self.dt = float(self.config['sim time settings']['custom sim time profile']['time step'])
            self.sim_end = float(self.config['sim time settings']['custom sim time profile']['total time'])
            self.sim_tsteps = self.sim_end/self.dt
            self.resample = float(self.config['sim time settings']['custom sim time profile']['sampling rate'])
            self.t_resample = self.resample/self.dt
            self.method = 0
            # self.gj_radius = float(self.config['sim time settings']['custom sim time profile']['gap junction radius'])
            # self.gjsa = math.pi*((self.gj_radius)**2)

def get_colormap(colormap_name: str) -> Colormap:
    '''
    Get the colormap with the passed name.
    '''
    colormap = getattr(cm, colormap_name, None)
    if not isinstance(colormap, Colormap):
        raise BetseExceptionParameters('matplotlib colormap "{}" unrecognized.'.format(colormap_name))
    return colormap

def bal_charge(concentrations,zs):

    q = 0

    for conc,z in zip(concentrations,zs):
        q = q+ conc*z

        to_zero = -q
        bal_conc = abs(to_zero)
        valance = np.sign(to_zero)

        assert bal_conc >= 0

    return bal_conc,valance


#FIXME: Cut me off at the knees, please.
    # def inbuiltInit(self):
    #     '''
    #     Initialize parameters to sane hardcoded defaults.
    #     The 'inbuiltInit' method is intended for in-house testing purposes when new functionality is built in
    #     but before it's added to the configuration file.
    #     '''
    #     self.time_profile_init = 'initialize'        # choose time profile for initialization sim
    #     self.time_profile_sim = 'simulate_somatic'   # choice of 'simulate_excitable' or 'simulate_somatic'
    #
    #     self.time4init = 5*60      # set the time for the initialization sim [s]
    #     self.time4sim = 0.5*60        # set total time for simulation [s]
    #
    #     # File saving
    #     self.init_path = os.path.expanduser("~/.betse/cache/100umInit/")  # world, inits, and sims are saved and read to/from this directory.
    #     self.sim_path = os.path.expanduser("~/.betse/cache/100umInit/sim_test") # folder to save unique simulation and data linked to init
    #     self.sim_results = os.path.expanduser("~/.betse/cache/100umInit/sim_test/results") # folder to auto-save results (graphs, images, animations)
    #
    #     # Geometric constants and factors
    #     self.wsx = 100e-6  # the x-dimension of the world space [m] recommended range 50 to 1000 um
    #     self.wsy = self.wsx  # the y-dimension of the world space [m] recommended range 50 to 1000 um
    #     self.rc = 5e-6  # radius of single cell
    #     self.cell_height = 5.0e-6  # the height of a cell in the z-direction (for volume and surface area calculations)
    #     self.cell_space = 26.0e-9  # the true cell-cell spacing (width of extracellular space)
    #     self.nl = 0.8  # noise level for the lattice
    #     self.vol_env = 2*self.wsx*self.wsy*self.cell_height    # volume of the environmental space [m3]
    #
    #     self.T = 310   # Cells temperature [K]
    #
    #     # gap junction constants and network connectivity
    #     self.search_d =1.5     # distance to search for nearest neighbours (relative to cell diameter dc) min 1.0 max 5.0
    #
    #     self.gj_vthresh = 60e-3              # cell-cell voltage threshhold at which gj close [V]
    #     self.gj_vgrad  = 30e-3               # the range over which gj goes from open to shut at threshold [V]
    #
    #     # set ion profile to be used: 'basic' (4 ions), 'basic_Ca' (5 ions), 'animal' (7 ions), 'invertebrate' (7 ions)
    #     self.ion_profile = 'animal'
    #
    #     # include full calcium dynamics in the situation (i.e. endoplasmic reticulum, etc)? Yes = 1, No =0
    #     self.Ca_dyn = 0
    #
    #     # include HK-ATPase in the simulation? Yes =1, No = 0
    #     self.HKATPase_dyn = 0
    #
    #     # include V-ATPase in the simulation? Yes =1, No = 0
    #     self.VATPase_dyn = 0
    #
    #     # include diffusion of a voltage sensitive dye? Yes = 1, No = 0
    #     self.voltage_dye = 0
    #
    #     self.Dm_Dye = 1.0e-12  # voltage sensitive dye membrane diffusion coefficient [m2/s]
    #     self.Do_Dye = 1.0e-9   # gap junction diffusion constant of voltage-sensitive dye [m2/s]
    #     self.z_Dye = 1         # charge valence of dye
    #     self.cDye_to = 1.0e-3    # initial concentration of voltage sensitive dye in environment [mol/m3]
    #
    #     # include noise in the simulation?
    #     self.channel_noise_level = 0   # static noise: adds a random scatter to the K+leak channels in the membrane (range 0 to 10)
    #
    #     self.dynamic_noise = 0         # dynamic noise: adds a random walk on the concentration of protein in the cell
    #     self.dynamic_noise_level = 1e-7   # dynamic noise level: how much dynamic noise: range 0 to 1e-6
    #
    # #..................................................................................................................
    #     # default membrane diffusion constants: easy control of cell's base resting potential
    #     self.Dm_Na = 1.0e-18     # membrane diffusion constant sodium [m2/s]
    #     self.Dm_K = 15.0e-18      # membrane diffusion constant potassium [m2/s]
    #     self.Dm_Cl = 2.0e-18     # membrane diffusion constant chloride [m2/s]
    #     self.Dm_Ca = 1.0e-18     # membrane diffusion constant calcium [m2/s]
    #     self.Dm_H = 1.0e-18      # membrane diffusion constant hydrogen [m2/s]
    #     self.Dm_M = 1.0e-18     # membrane diffusion constant anchor ion [m2/s]
    #     self.Dm_P = 0.0        # membrane diffusion constant proteins [m2/s]
    #
    #     #.............................Scheduled Interventions..........................................................
    #
    #     # Schedule global changes to all cells in the collective:
    #     self.global_options = {'K_env':0,'Cl_env':0,'Na_env':0,'gj_block':0,'T_change':0,'NaKATP_block':0,
    #         'HKATP_block':0}
    #     # K_env, Cl_env, Na_env, T_change: [time on, time off, rate change, multiplier]
    #     # gj_block, NaKATP_block,HKATP_block, CaATP_block: [time on, time off, rate change]
    #
    #     # cell to effect in scheduled intervention: (choices = 'none','all','random1','random50', [1,2,3])
    #     self.scheduled_targets = [0]    # targets do not affect: gj_block,T_change, NaKATP_block, HKATP_block,CaATP_block,CaER_block
    #
    #     #self.ion_options specifications list is [time on, time off, rate of change, multiplier]
    #     self.scheduled_options = {'Na_mem':0,'K_mem':0,'Cl_mem':0,'Ca_mem':0,'K_env':0,'Cl_env':0,
    #         'IP3':[5,15,1,1e-4]}
    #
    #     #...................................Voltage Gated Channels......................................................
    #
    #     # cells to effect with voltage gated channels: (choices = 'none','all','random1','random50', [1,2,3])
    #     self.gated_targets = 'none'
    #     # self.vg_options specifications list for voltage gated ion channel options:
    #     vgNa = [1.0e-15,-50e-3,30e-3,-52e-3,5e-3,10e-3]  # [max Na mem diffusion m2/s, v on, v inactive, v deactivate,duration active (s), duration inactive]
    #     vgK = [0.5e-15, -20e-3,-75e-3,10.0e-3]           # [max K mem diffusion (m2/s), v on, v off, duration (s)]
    #     vgCa = [1.0e-15,-40e-3,40e-3,0.75e-3,200.0e-6]  # [maxCa mem diffusion m2/s, v on, v off, Ca2+ off mmol/L, Ca2+ reactivate]
    #     cagK = [2.0e-16,7.5e-4,3]                    # [maxK mem diffusion (m2/s), half-max Ca2+ for gating, hill coefficient]
    #
    #     self.vg_options = {'Na_vg':0,'K_vg':0,'Ca_vg':0,'K_cag':0}
    #
    #     # Calcium TissueHandler: Calcium Induced Calcium Release (CICR) and Store Operated Calcium Entry (SOCE)..............
    #
    #
    #     ERstore_dyn = [5e-15,0.8,0.5]   # base dynamics of endoplasmic reticulum Ca2+ store:
    #                                     # [max diffusion m2/s, full Ca thresh mol/m3, empty Ca thresh mol/m3]
    #     ca_reg = []   # central concentration for Ca-act-Ca release [Ca mid, Ca width]
    #     #ca_reg =[]                  # leave this empty to have no Ca-influence on the dynamics
    #
    #     ip3_reg = [1e-3,3.4]   # max Ca2+ diffusion constant through ER membrane, IP3 half-max, Hill coefficient
    #     #ip3_reg = []            # leave this empty to have no ip3-influence on the dynamics
    #     self.FMmod = 1              # frequency modulate ER response to IP3? 1 = yes, 0 = no
    #     self.ip3FM = 0.8            # degree to which ip3 affects Ca2+ frequency (higher more effect, max 0.9)
    #
    #
    #     cicr = [ERstore_dyn,ca_reg,ip3_reg]
    #     self.Ca_dyn_options = {'CICR':0}
    #
    #     self.Dm_IP3 = 1.0e-18   # membrane diffusion constant of IP3
    #     self.Do_IP3 = 1.0e-5    # IP3 free diffusion constant [m2/s] (this is artificially high due to gj being artificially low)
    #     self.z_IP3 = -3        # charge valence of IP3
    #     self.cIP3_to = 1e-6     # initial value of IP3 in all cells
    #     self.cIP3_to_env = 1e-6  # initial value of IP3 in environment
    #
    #     #..........................PLOTTING OPTIONS and OUTPUT..........................................................
    #
    #     self.turn_all_plots_off = False    # turn off all plots and animations for init and sim runs
    #
    #      # Default colormap
    #     self.default_cm = cm.coolwarm   # options include cm.rainbow, cm.jet, cm.Blues, cm.Greens, see:
    #                                     # http://matplotlib.org/examples/color/colormaps_reference.html
    #
    #     self.gj_cm = cm.bone           # colormap for plotting gj currents on top of default colormap
    #
    #     self.plot_while_solving = True  # create a 2d plot of cell vmems while solution is taking place
    #     self.save_solving_plot = False   # save the 2d plot generated while solving (warning: will slow sim down!)
    #
    #     self.enumerate_cells = False    # number cells on the static 2D maps with their simulation index (this can help
    #                                     # decide on the value of self.plot_cell
    #
    #     self.plot_cell = 11             # State the cell index to use for single-cell time plots
    #
    #     self.plot_single_cell_graphs = True # plot graphs of concentration and voltage in self.plot_cell with time
    #
    #     self.showCells = True     # plots and ani are individual cell plots if True; as interpolated mesh data if False
    #
    #     self.plot_vm2d = True                # 2d plot of final vmem ?
    #     self.plot_ca2d = False                # 2d plot of final cell calcium ?
    #     self.plot_ip32d = False               # 2d plot of final cIP3 ?
    #     self.plot_dye2d = False               # 2d plot of voltage sensitive dye in cell collective?
    #
    #     self.createAnimations = True   # create all animations = True; turn off all animations = False
    #
    #     # specify desired animations:
    #     self.ani_vm2d = True              # 2d animation of vmem with time?
    #     self.ani_ca2d = False             # 2d animation of cell calcium with time ?
    #     self.ani_ip32d = False            # 2d animation of cIP3 with time?
    #     self.ani_dye2d = False            # 2d animation of voltage sensitive dye in cell collective with time?
    #     self.ani_vmgj2d = False           # 2d animation of vmem with superimposed gj network showing current direction
    #
    #     self.autosave = True           # autosave all still images to a results directory in the simulation folder
    #     self.saveAnimations = True    # save all animations as png sequences in animation-specific folders
    #
    #     self.exportData = True        # export all stored data for the plot_cell to a csv text file
    #
    #     self.clip = 20e-6
    #
    #     # ........................Rarely changed constants and calculations.............................................
    #
    #     # default free diffusion constants (cytoplasmic)
    #     self.Do_Na = 1.33e-9      # free diffusion constant sodium [m2/s]
    #     self.Do_K = 1.96e-9      # free diffusion constant potassium [m2/s]
    #     self.Do_Cl = 2.03e-9     # free diffusion constant chloride [m2/s]
    #     self.Do_Ca = 1.0e-10     # free diffusion constant calcium [m2/s]
    #     self.Do_H = 2.5e-9      # free diffusion constant hydrogen [m2/s]
    #     self.Do_M = 1.0e-9     # free diffusion constant mystery anchor ion [m2/s]
    #     self.Do_P = 5.0e-10      # free diffusion constant protein [m2/s]
    #
    #     # pump parameters
    #     self.alpha_NaK = 5.0e-8 # maximum rate constant sodium-potassium ATPase per unit surface area [1/mol*s] (range 1e-17 to 5e-16)
    #     self.halfmax_NaK = 12   # the free energy level at which pump activity is halved [kJ]
    #     self.slope_NaK = 24  # the energy window width of the NaK-ATPase pump [kJ]
    #
    #     self.alpha_Ca = 2.5e-5 # pump rate for calcium ATPase in membrane [1/mol*s] 2.0e-15
    #     self.alpha_CaER = 1.0e-3  # pump rate for calcium ATPase in endoplasmic reticulum
    #     self.halfmax_Ca = 12
    #     self.slope_Ca = 24
    #
    #     self.alpha_HK = 1.0e-3  # pump rate for the H-K-ATPase per unit surface area [1/mol*s] range 5.oe-4 to 2.5e-3
    #     self.halfmax_HK = 12
    #     self.slope_HK = 24
    #
    #     self.alpha_V = 2.0e-4  # pump rate for the V-ATPase per unit surface area [1/mol*s] range 5.oe-4 to 2.5e-3
    #     self.halfmax_V = 12
    #     self.slope_V = 24
    #
    #      # Endoplasmic reticulum
    #     self.ER_vol = 0.1                  # volume of endoplasmic reticulum as a fraction of cell volume
    #     self.ER_sa = 1.0                    # surface area of endoplasmic reticulum as a fraction of cell surface area
    #
    #     # partial pressure dissolved CO2
    #     self.CO2 = 50   # [mmHg]
    #
    #     # charge states of ions
    #     self.z_Na = 1
    #     self.z_K = 1
    #     self.z_Cl = -1
    #     self.z_Ca = 2
    #     self.z_H = 1
    #     self.z_P = -1
    #     self.z_M = -1
    #
    #     # fundamental constants
    #     self.F = 96485 # Faraday constant [J/V*mol]
    #     self.R = 8.314  # Gas constant [J/K*mol]
    #
    #     self.deltaGATP = 20*self.R*self.T    # free energy released in ATP hydrolysis [J/mol]
    #
    #     self.ac = 1e-6  # cell-cell separation for drawing
    #     self.scale_cell = 0.9          # the amount to scale cell membranes in from ecm edges (only affects drawing)
    #     self.cm = 0.022            # patch capacitance of cell membrane up to 0.022 [F/m2]
    #     self.tm = 7.5e-9           # thickness of cell membrane [m]
    #     self.cell_sides = 4      # minimum number of membrane domains per cell (must be >2)
    #     self.scale_alpha = 1.0   # the amount to scale (1/d_cell) when calculating the concave hull (boundary search)
    #
    #     self.d_cell = self.rc * 2  # diameter of single cell
    #     self.nx = int(self.wsx / self.d_cell)  # number of lattice sites in world x index
    #     self.ny = int(self.wsy / self.d_cell)  # number of lattice sites in world y index
    #     self.wsx = self.wsx + 5 * self.nl * self.d_cell  # readjust the world size for noise
    #     self.wsy = self.wsy + 5 * self.nl * self.d_cell
    #
    #     self.gjl = 2*self.tm + self.cell_space     # gap junction length
    #
    #
    #     self.um = 1e6    # multiplication factor to convert m to um
    #
    #     # simplest ion ion_profile giving realistic results with minimal ions (Na+ & K+ focus):
    #     if self.ion_profile == 'basic':
    #
    #         self.cNa_env = 145.0
    #         self.cK_env = 5.0
    #         self.cP_env = 9.0
    #
    #         zs = [self.z_Na, self.z_K, self.z_P]
    #
    #         conc_env = [self.cNa_env,self.cK_env, self.cP_env]
    #         self.cM_env, self.z_M_env = bal_charge(conc_env,zs)
    #
    #         assert self.z_M_env == -1
    #
    #         self.cNa_cell = 5.4
    #         self.cK_cell = 140.44
    #         self.cP_cell = 138.0
    #
    #         conc_cell = [self.cNa_cell,self.cK_cell, self.cP_cell]
    #
    #         self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)
    #
    #         assert self.z_M_cell == -1
    #
    #         self.ions_dict = {'Na':1,'K':1,'Cl':0,'Ca':0,'H':0,'P':1,'M':1}
    #
    #
    #     if self.ion_profile == 'basic_Ca':
    #
    #         self.cNa_env = 145.0
    #         self.cK_env = 5.0
    #         self.cCa_env = 1.0
    #         self.cP_env = 9.0
    #
    #         zs = [self.z_Na, self.z_K, self.z_Ca, self.z_P]
    #
    #         conc_env = [self.cNa_env,self.cK_env, self.cCa_env, self.cP_env]
    #         self.cM_env, self.z_M_env = bal_charge(conc_env,zs)
    #
    #         assert self.z_M_env == -1
    #
    #         self.cNa_cell = 5.4
    #         self.cK_cell = 140.44
    #         self.cCa_cell = 1.0
    #         self.cP_cell = 138.0
    #
    #         conc_cell = [self.cNa_cell,self.cK_cell, self.cCa_cell, self.cP_cell]
    #
    #         self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)
    #
    #         assert self.z_M_cell == -1
    #
    #         self.cCa_er = 1.0
    #         self.cM_er = self.cCa_er
    #
    #         self.ions_dict = {'Na':1,'K':1,'Cl':0,'Ca':1,'H':0,'P':1,'M':1}
    #
    #     # default environmental and cytoplasmic initial values mammalian cells
    #     if self.ion_profile == 'animal':
    #
    #         self.cNa_env = 145.0
    #         self.cK_env = 5.0
    #         self.cCl_env = 105.0
    #         self.cCa_env = 1.0
    #         self.cH_env = 3.98e-5
    #         self.cP_env = 9.0
    #
    #         zs = [self.z_Na, self.z_K, self.z_Cl, self.z_Ca, self.z_H, self.z_P]
    #
    #         conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cCa_env, self.cH_env, self.cP_env]
    #         self.cM_env, self.z_M_env = bal_charge(conc_env,zs)
    #
    #         assert self.z_M_env == -1
    #
    #         self.cNa_cell = 5.4
    #         self.cK_cell = 140.44
    #         self.cCl_cell = 6.0
    #         self.cCa_cell = 1.0
    #         self.cH_cell = 6.31e-5
    #         self.cP_cell = 138.0
    #
    #         conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell, self.cCa_cell, self.cH_cell, self.cP_cell]
    #         self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)
    #
    #         assert self.z_M_cell == -1
    #
    #         self.cCa_er = 1.0
    #         self.cM_er = - self.cCa_er
    #
    #         self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':1,'H':1,'P':1,'M':1}
    #
    #      # default environmental and cytoplasm values invertebrate cells
    #     if self.ion_profile == 'invertebrate':
    #         self.cNa_env = 440.0
    #         self.cK_env = 20.0
    #         self.cCl_env = 460.0
    #         self.cCa_env = 10.0
    #         self.cH_env = 3.98e-5
    #         self.cP_env = 7.0
    #
    #         zs = [self.z_Na, self.z_K, self.z_Cl, self.z_Ca, self.z_H, self.z_P]
    #
    #         conc_env = [self.cNa_env,self.cK_env, self.cCl_env, self.cCa_env, self.cH_env, self.cP_env]
    #         self.cM_env, self.z_M_env = bal_charge(conc_env,zs)
    #
    #         assert self.z_M_env == -1
    #
    #         self.cNa_cell = 8.66
    #         self.cK_cell = 406.09
    #         self.cCl_cell = 45.56
    #         # self.cCa_cell = 3.0e-4
    #         self.cCa_cell = 10.0
    #         self.cH_cell = 6.31e-5
    #         self.cP_cell = 350.0
    #
    #         conc_cell = [self.cNa_cell,self.cK_cell, self.cCl_cell, self.cCa_cell, self.cH_cell, self.cP_cell]
    #         self.cM_cell, self.z_M_cell = bal_charge(conc_cell,zs)
    #
    #         assert self.z_M_cell == -1
    #
    #         self.cCa_er = 10.0
    #         self.cM_er = -self.cCa_er
    #
    #         self.ions_dict = {'Na':1,'K':1,'Cl':1,'Ca':1,'H':1,'P':1,'M':1}
