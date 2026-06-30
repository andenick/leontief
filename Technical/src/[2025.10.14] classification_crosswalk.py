#!/usr/bin/env python3
"""
Classification Cross-Walk Module for Leontief
Leontief - Industry Classification Harmonization

This module provides cross-walk functionality between different industry
classification systems, enabling harmonization across international I-O databases.

Key Features:
- ISIC Rev. 4 to NAICS conversion
- OECD ICIO 36-sector to BEA NAICS mapping
- WIOD ISIC Rev. 3 to NAICS conversion
- Custom classification mapping tools
- Quality assessment and validation

Author: Claude Code Assistant
Date: 2025-10-14
Version: 1.0
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Set
import logging
from datetime import datetime
import json
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ClassificationCrossWalk:
    """
    Industry Classification Cross-Walk System

    Provides comprehensive mapping between different industry classification
    systems used in I-O databases, enabling data harmonization and comparison.

    Supported Classifications:
    - ISIC Rev. 4 (OECD ICIO, 36 sectors)
    - ISIC Rev. 3 (WIOD, 56 sectors)
    - NAICS (BEA, 71 categories and detailed)
    - NACE Rev. 2 (European)
    """

    def __init__(self, base_path: str = None):
        """
        Initialize Classification Cross-Walk System

        Args:
            base_path (str): Base path for cross-walk data storage
        """
        self.base_path = Path(base_path) if base_path else (Path(os.environ.get("DATA_ROOT", ".")) / "Technical/data/classifications")

        # Initialize classification systems
        self.isic_rev4_sectors = self._get_isic_rev4_sectors()
        self.isic_rev3_sectors = self._get_isic_rev3_sectors()
        self.naics_sectors = self._get_naics_sectors()

        # Cross-walk mappings
        self.isic4_to_naics = {}
        self.isic3_to_naics = {}
        self.naics_to_isic4 = {}
        self.naics_to_isic3 = {}

        # Quality metrics
        self.mapping_quality = {}
        self.coverage_stats = {}

        # Create directories
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info("Classification Cross-Walk System initialized")
        logger.info(f"ISIC Rev. 4 sectors: {len(self.isic_rev4_sectors)}")
        logger.info(f"ISIC Rev. 3 sectors: {len(self.isic_rev3_sectors)}")
        logger.info(f"NAICS sectors: {len(self.naics_sectors)}")

    def _get_isic_rev4_sectors(self) -> Dict[str, Dict]:
        """Get ISIC Rev. 4 classification sectors (OECD ICIO 36-sector)"""
        return {
            'A01': {
                'name': 'Crop and animal production, hunting and related service activities',
                'code': 'A01',
                'description': 'Agriculture, forestry and fishing',
                'naics_mapping': ['111', '112']
            },
            'A02': {
                'name': 'Forestry and logging',
                'code': 'A02',
                'description': 'Forestry and logging',
                'naics_mapping': ['113']
            },
            'A03': {
                'name': 'Fishing and aquaculture',
                'code': 'A03',
                'description': 'Fishing, hunting and trapping',
                'naics_mapping': ['114']
            },
            'B': {
                'name': 'Mining and quarrying',
                'code': 'B',
                'description': 'Mining, quarrying, and oil and gas extraction',
                'naics_mapping': ['21']
            },
            'C10-C12': {
                'name': 'Food products, beverages and tobacco',
                'code': 'C10-C12',
                'description': 'Food manufacturing',
                'naics_mapping': ['311']
            },
            'C13-C15': {
                'name': 'Textiles, wearing apparel, leather and related products',
                'code': 'C13-C15',
                'description': 'Textile and apparel manufacturing',
                'naics_mapping': ['313', '315', '316']
            },
            'C16': {
                'name': 'Wood and products of wood and cork',
                'code': 'C16',
                'description': 'Wood product manufacturing',
                'naics_mapping': ['321']
            },
            'C17_C18': {
                'name': 'Paper and paper products; printing and reproduction of recorded media',
                'code': 'C17_C18',
                'description': 'Paper and printing manufacturing',
                'naics_mapping': ['322', '323']
            },
            'C19': {
                'name': 'Coke and refined petroleum products',
                'code': 'C19',
                'description': 'Petroleum and coal products manufacturing',
                'naics_mapping': ['324']
            },
            'C20_C21': {
                'name': 'Chemicals and chemical products',
                'code': 'C20_C21',
                'description': 'Chemical manufacturing',
                'naics_mapping': ['325']
            },
            'C22': {
                'name': 'Basic pharmaceutical products and pharmaceutical preparations',
                'code': 'C22',
                'description': 'Pharmaceutical and medicine manufacturing',
                'naics_mapping': ['3254']
            },
            'C23': {
                'name': 'Rubber and plastics products',
                'code': 'C23',
                'description': 'Rubber and plastics manufacturing',
                'naics_mapping': ['326']
            },
            'C24': {
                'name': 'Other non-metallic mineral products',
                'code': 'C24',
                'description': 'Nonmetallic mineral product manufacturing',
                'naics_mapping': ['327']
            },
            'C25': {
                'name': 'Basic metals',
                'code': 'C25',
                'description': 'Primary metal manufacturing',
                'naics_mapping': ['331']
            },
            'C26': {
                'name': 'Fabricated metal products, except machinery and equipment',
                'code': 'C26',
                'description': 'Fabricated metal product manufacturing',
                'naics_mapping': ['332']
            },
            'C27': {
                'name': 'Computer, electronic and optical products',
                'code': 'C27',
                'description': 'Computer and electronic product manufacturing',
                'naics_mapping': ['334']
            },
            'C28': {
                'name': 'Electrical equipment',
                'code': 'C28',
                'description': 'Electrical equipment, appliance, and component manufacturing',
                'naics_mapping': ['335']
            },
            'C29': {
                'name': 'Machinery and equipment n.e.c.',
                'code': 'C29',
                'description': 'Machinery manufacturing',
                'naics_mapping': ['333']
            },
            'C30': {
                'name': 'Motor vehicles, trailers and semi-trailers',
                'code': 'C30',
                'description': 'Transportation equipment manufacturing - motor vehicles',
                'naics_mapping': ['3361', '3362', '3363']
            },
            'C31_C32': {
                'name': 'Other transport equipment',
                'code': 'C31_C32',
                'description': 'Transportation equipment manufacturing - other',
                'naics_mapping': ['3364', '3365', '3366', '3369']
            },
            'C33': {
                'name': 'Furniture; other manufacturing',
                'code': 'C33',
                'description': 'Furniture and related product manufacturing',
                'naics_mapping': ['337']
            },
            'D': {
                'name': 'Electricity, gas, steam and air conditioning supply',
                'code': 'D',
                'description': 'Utilities',
                'naics_mapping': ['22']
            },
            'E': {
                'name': 'Water supply, sewerage, waste management and remediation activities',
                'code': 'E',
                'description': 'Water and waste management',
                'naics_mapping': ['221', '562']
            },
            'F': {
                'name': 'Construction',
                'code': 'F',
                'description': 'Construction',
                'naics_mapping': ['23']
            },
            'G45': {
                'name': 'Wholesale and retail trade; repair of motor vehicles and motorcycles',
                'code': 'G45',
                'description': 'Wholesale trade',
                'naics_mapping': ['42']
            },
            'G46': {
                'name': 'Wholesale trade, except of motor vehicles and motorcycles',
                'code': 'G46',
                'description': 'Retail trade',
                'naics_mapping': ['44', '45']
            },
            'H': {
                'name': 'Transportation and storage',
                'code': 'H',
                'description': 'Transportation and warehousing',
                'naics_mapping': ['48', '49']
            },
            'I': {
                'name': 'Accommodation and food service activities',
                'code': 'I',
                'description': 'Accommodation and food services',
                'naics_mapping': ['72']
            },
            'J58_J60': {
                'name': 'Publishing, audiovisual and broadcasting activities',
                'code': 'J58_J60',
                'description': 'Information and publishing',
                'naics_mapping': ['511', '512', '515']
            },
            'J61': {
                'name': 'Telecommunications',
                'code': 'J61',
                'description': 'Telecommunications',
                'naics_mapping': ['517']
            },
            'J62_J63': {
                'name': 'Information technology and other information services',
                'code': 'J62_J63',
                'description': 'Data processing, hosting, and related services',
                'naics_mapping': ['518', '519']
            },
            'K': {
                'name': 'Financial and insurance activities',
                'code': 'K',
                'description': 'Finance and insurance',
                'naics_mapping': ['52']
            },
            'L': {
                'name': 'Real estate activities',
                'code': 'L',
                'description': 'Real estate and rental and leasing',
                'naics_mapping': ['53']
            },
            'M_N': {
                'name': 'Professional, scientific and technical activities; Administrative and support service activities',
                'code': 'M_N',
                'description': 'Professional, scientific, and technical services',
                'naics_mapping': ['54', '55', '56']
            },
            'O': {
                'name': 'Public administration and defence; compulsory social security',
                'code': 'O',
                'description': 'Public administration',
                'naics_mapping': ['92']
            },
            'P': {
                'name': 'Education',
                'code': 'P',
                'description': 'Educational services',
                'naics_mapping': ['61']
            },
            'Q': {
                'name': 'Human health and social work activities',
                'code': 'Q',
                'description': 'Health care and social assistance',
                'naics_mapping': ['62']
            },
            'R_S': {
                'name': 'Arts, entertainment and recreation; Other services',
                'code': 'R_S',
                'description': 'Arts, entertainment, and recreation',
                'naics_mapping': ['71', '81']
            },
            'T': {
                'name': 'Activities of households as employers; undifferentiated goods and services-producing activities of households for own use',
                'code': 'T',
                'description': 'Private households',
                'naics_mapping': ['814']
            }
        }

    def _get_isic_rev3_sectors(self) -> Dict[str, Dict]:
        """Get ISIC Rev. 3 classification sectors (WIOD 56-sector)"""
        return {
            'atb': {
                'name': 'Agriculture, Hunting, Forestry and Fishing',
                'code': 'atb',
                'description': 'Primary sector activities',
                'naics_mapping': ['11', '21', '113']
            },
            'c': {
                'name': 'Mining and Quarrying',
                'code': 'c',
                'description': 'Mining and extraction',
                'naics_mapping': ['21']
            },
            '15t16': {
                'name': 'Food, Beverages and Tobacco',
                'code': '15t16',
                'description': 'Food manufacturing',
                'naics_mapping': ['311']
            },
            '17t18': {
                'name': 'Textiles, Textile Products, Leather and Footwear',
                'code': '17t18',
                'description': 'Textile and apparel',
                'naics_mapping': ['313', '315', '316']
            },
            '19': {
                'name': 'Wood and Products of Wood and Cork',
                'code': '19',
                'description': 'Wood products',
                'naics_mapping': ['321']
            },
            '20t21': {
                'name': 'Pulp, Paper, Paper Products, Printing and Publishing',
                'code': '20t21',
                'description': 'Paper and printing',
                'naics_mapping': ['322', '323']
            },
            '22t23': {
                'name': 'Coke, Refined Petroleum and Nuclear Fuel; Chemicals and Chemical Products',
                'code': '22t23',
                'description': 'Chemical and petroleum products',
                'naics_mapping': ['324', '325']
            },
            '24': {
                'name': 'Rubber and Plastics',
                'code': '24',
                'description': 'Rubber and plastics',
                'naics_mapping': ['326']
            },
            '25': {
                'name': 'Other Non-Metallic Mineral',
                'code': '25',
                'description': 'Non-metallic minerals',
                'naics_mapping': ['327']
            },
            '26': {
                'name': 'Basic Metals and Fabricated Metal',
                'code': '26',
                'description': 'Metal manufacturing',
                'naics_mapping': ['331', '332']
            },
            '27t28': {
                'name': 'Machinery, Nec',
                'code': '27t28',
                'description': 'Machinery and equipment',
                'naics_mapping': ['333']
            },
            '29': {
                'name': 'Electrical and Optical Equipment',
                'code': '29',
                'description': 'Electronics and electrical equipment',
                'naics_mapping': ['334', '335']
            },
            '30t33': {
                'name': 'Transport Equipment',
                'code': '30t33',
                'description': 'Transportation equipment',
                'naics_mapping': ['336']
            },
            '34t35': {
                'name': 'Manufacturing, Nec; Recycling',
                'code': '34t35',
                'description': 'Other manufacturing',
                'naics_mapping': ['337', '339']
            },
            'e': {
                'name': 'Electricity, Gas and Water Supply',
                'code': 'e',
                'description': 'Utilities',
                'naics_mapping': ['22']
            },
            'f': {
                'name': 'Construction',
                'code': 'f',
                'description': 'Construction',
                'naics_mapping': ['23']
            },
            '50': {
                'name': 'Sale, Maintenance and Repair of Motor Vehicles and Motorcycles; Retail Sale of Fuel',
                'code': '50',
                'description': 'Motor vehicle trade',
                'naics_mapping': ['441']
            },
            '51': {
                'name': 'Wholesale Trade and Commission Trade, Except of Motor Vehicles and Motorcycles',
                'code': '51',
                'description': 'Wholesale trade',
                'naics_mapping': ['42']
            },
            '52': {
                'name': 'Retail Trade, Except of Motor Vehicles and Motorcycles; Repair of Household Goods',
                'code': '52',
                'description': 'Retail trade',
                'naics_mapping': ['44', '45']
            },
            'h': {
                'name': 'Hotels and Restaurants',
                'code': 'h',
                'description': 'Accommodation and food services',
                'naics_mapping': ['72']
            },
            '60': {
                'name': 'Inland Transport',
                'code': '60',
                'description': 'Land transportation',
                'naics_mapping': ['482', '483', '484', '485', '486', '487', '488']
            },
            '61': {
                'name': 'Water Transport',
                'code': '61',
                'description': 'Water transportation',
                'naics_mapping': ['483']
            },
            '62': {
                'name': 'Air Transport',
                'code': '62',
                'description': 'Air transportation',
                'naics_mapping': ['481']
            },
            '63': {
                'name': 'Other Supporting and Auxiliary Transport Activities; Activities of Travel Agencies',
                'code': '63',
                'description': 'Transportation support',
                'naics_mapping': ['487', '488']
            },
            '64': {
                'name': 'Post and Telecommunications',
                'code': '64',
                'description': 'Communications',
                'naics_mapping': ['51', '517', '518']
            },
            'j': {
                'name': 'Financial Intermediation',
                'code': 'j',
                'description': 'Finance and insurance',
                'naics_mapping': ['52']
            },
            '70': {
                'name': 'Real Estate Activities',
                'code': '70',
                'description': 'Real estate',
                'naics_mapping': ['53']
            },
            '71t74': {
                'name': 'Renting of M&Eq and Other Business Activities',
                'code': '71t74',
                'description': 'Professional and business services',
                'naics_mapping': ['54', '55', '56']
            },
            'l': {
                'name': 'Public Admin and Defence; Compulsory Social Security',
                'code': 'l',
                'description': 'Public administration',
                'naics_mapping': ['92']
            },
            'm': {
                'name': 'Education',
                'code': 'm',
                'description': 'Education',
                'naics_mapping': ['61']
            },
            'n': {
                'name': 'Health and Social Work',
                'code': 'n',
                'description': 'Health care and social assistance',
                'naics_mapping': ['62']
            },
            'o': {
                'name': 'Other Community, Social and Personal Services',
                'code': 'o',
                'description': 'Other services',
                'naics_mapping': ['81']
            },
            'p': {
                'name': 'Private Households with Employed Persons',
                'code': 'p',
                'description': 'Private households',
                'naics_mapping': ['814']
            }
        }

    def _get_naics_sectors(self) -> Dict[str, Dict]:
        """Get NAICS classification sectors (BEA 71-category and detailed)"""
        return {
            '11': {
                'name': 'Agriculture, Forestry, Fishing and Hunting',
                'code': '11',
                'description': 'Agricultural sector',
                'isic4_mapping': ['A01', 'A02', 'A03']
            },
            '21': {
                'name': 'Mining, Quarrying, and Oil and Gas Extraction',
                'code': '21',
                'description': 'Mining sector',
                'isic4_mapping': ['B']
            },
            '22': {
                'name': 'Utilities',
                'code': '22',
                'description': 'Utilities sector',
                'isic4_mapping': ['D']
            },
            '23': {
                'name': 'Construction',
                'code': '23',
                'description': 'Construction sector',
                'isic4_mapping': ['F']
            },
            '31-33': {
                'name': 'Manufacturing',
                'code': '31-33',
                'description': 'All manufacturing',
                'isic4_mapping': ['C10-C12', 'C13-C15', 'C16', 'C17_C18', 'C19', 'C20_C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29', 'C30', 'C31_C32', 'C33']
            },
            '42': {
                'name': 'Wholesale Trade',
                'code': '42',
                'description': 'Wholesale trade',
                'isic4_mapping': ['G46']
            },
            '44-45': {
                'name': 'Retail Trade',
                'code': '44-45',
                'description': 'Retail trade',
                'isic4_mapping': ['G45']
            },
            '48-49': {
                'name': 'Transportation and Warehousing',
                'code': '48-49',
                'description': 'Transportation and warehousing',
                'isic4_mapping': ['H']
            },
            '51': {
                'name': 'Information',
                'code': '51',
                'description': 'Information sector',
                'isic4_mapping': ['J58_J60', 'J61', 'J62_J63']
            },
            '52': {
                'name': 'Finance and Insurance',
                'code': '52',
                'description': 'Finance and insurance',
                'isic4_mapping': ['K']
            },
            '53': {
                'name': 'Real Estate and Rental and Leasing',
                'code': '53',
                'description': 'Real estate',
                'isic4_mapping': ['L']
            },
            '54': {
                'name': 'Professional, Scientific, and Technical Services',
                'code': '54',
                'description': 'Professional services',
                'isic4_mapping': ['M_N']
            },
            '55': {
                'name': 'Management of Companies and Enterprises',
                'code': '55',
                'description': 'Management',
                'isic4_mapping': ['M_N']
            },
            '56': {
                'name': 'Administrative and Support and Waste Management and Remediation Services',
                'code': '56',
                'description': 'Administrative services',
                'isic4_mapping': ['E', 'M_N']
            },
            '61': {
                'name': 'Educational Services',
                'code': '61',
                'description': 'Education',
                'isic4_mapping': ['P']
            },
            '62': {
                'name': 'Health Care and Social Assistance',
                'code': '62',
                'description': 'Health care',
                'isic4_mapping': ['Q']
            },
            '71': {
                'name': 'Arts, Entertainment, and Recreation',
                'code': '71',
                'description': 'Arts and entertainment',
                'isic4_mapping': ['R_S']
            },
            '72': {
                'name': 'Accommodation and Food Services',
                'code': '72',
                'description': 'Accommodation and food',
                'isic4_mapping': ['I']
            },
            '81': {
                'name': 'Other Services (except Public Administration)',
                'code': '81',
                'description': 'Other services',
                'isic4_mapping': ['R_S']
            },
            '92': {
                'name': 'Public Administration',
                'code': '92',
                'description': 'Government',
                'isic4_mapping': ['O']
            }
        }

    def create_isic4_to_naics_crosswalk(self) -> pd.DataFrame:
        """
        Create comprehensive ISIC Rev. 4 to NAICS cross-walk table

        Returns:
            pd.DataFrame: Cross-walk table with mapping details and quality metrics
        """
        logger.info("Creating ISIC Rev. 4 to NAICS cross-walk...")

        crosswalk_data = []

        for isic_code, isic_info in self.isic_rev4_sectors.items():
            # Get mapped NAICS codes
            naics_codes = isic_info.get('naics_mapping', [])

            for naics_code in naics_codes:
                naics_info = self.naics_sectors.get(naics_code[:2], {})
                if naics_info:
                    # Assess mapping quality
                    quality_score = self._assess_mapping_quality(isic_code, naics_code)
                    coverage = self._calculate_coverage(isic_code, naics_code)

                    crosswalk_data.append({
                        'ISIC4_Code': isic_code,
                        'ISIC4_Name': isic_info['name'],
                        'ISIC4_Description': isic_info['description'],
                        'NAICS_Code': naics_code,
                        'NAICS_Name': naics_info.get('name', 'Unknown'),
                        'NAICS_Description': naics_info.get('description', 'Unknown'),
                        'Mapping_Quality': quality_score,
                        'Coverage_Percentage': coverage,
                        'Mapping_Type': self._determine_mapping_type(isic_code, naics_code),
                        'Comments': self._generate_mapping_comments(isic_code, naics_code)
                    })

        crosswalk_df = pd.DataFrame(crosswalk_data)

        # Save cross-walk table
        crosswalk_file = self.base_path / 'ISIC4_to_NAICS_crosswalk.csv'
        crosswalk_df.to_csv(crosswalk_file, index=False)

        logger.info(f"ISIC Rev. 4 to NAICS cross-walk created: {crosswalk_df.shape}")

        return crosswalk_df

    def create_isic3_to_naics_crosswalk(self) -> pd.DataFrame:
        """
        Create ISIC Rev. 3 to NAICS cross-walk table (for WIOD compatibility)

        Returns:
            pd.DataFrame: ISIC Rev. 3 to NAICS cross-walk table
        """
        logger.info("Creating ISIC Rev. 3 to NAICS cross-walk...")

        crosswalk_data = []

        for isic_code, isic_info in self.isic_rev3_sectors.items():
            naics_codes = isic_info.get('naics_mapping', [])

            for naics_code in naics_codes:
                naics_info = self.naics_sectors.get(naics_code[:2], {})
                if naics_info:
                    quality_score = self._assess_mapping_quality(isic_code, naics_code, 'isic3')
                    coverage = self._calculate_coverage(isic_code, naics_code, 'isic3')

                    crosswalk_data.append({
                        'ISIC3_Code': isic_code,
                        'ISIC3_Name': isic_info['name'],
                        'ISIC3_Description': isic_info['description'],
                        'NAICS_Code': naics_code,
                        'NAICS_Name': naics_info.get('name', 'Unknown'),
                        'NAICS_Description': naics_info.get('description', 'Unknown'),
                        'Mapping_Quality': quality_score,
                        'Coverage_Percentage': coverage,
                        'Mapping_Type': self._determine_mapping_type(isic_code, naics_code, 'isic3'),
                        'Comments': self._generate_mapping_comments(isic_code, naics_code, 'isic3')
                    })

        crosswalk_df = pd.DataFrame(crosswalk_data)

        # Save cross-walk table
        crosswalk_file = self.base_path / 'ISIC3_to_NAICS_crosswalk.csv'
        crosswalk_df.to_csv(crosswalk_file, index=False)

        logger.info(f"ISIC Rev. 3 to NAICS cross-walk created: {crosswalk_df.shape}")

        return crosswalk_df

    def _assess_mapping_quality(self, source_code: str, target_code: str, source_type: str = 'isic4') -> float:
        """
        Assess the quality of mapping between classification codes

        Args:
            source_code (str): Source classification code
            target_code (str): Target classification code
            source_type (str): Type of source classification ('isic4' or 'isic3')

        Returns:
            float: Quality score (0.0 to 1.0)
        """
        # Quality assessment based on:
        # 1. Conceptual similarity (0.3 weight)
        # 2. Coverage overlap (0.4 weight)
        # 3. Historical compatibility (0.3 weight)

        conceptual_similarity = self._calculate_conceptual_similarity(source_code, target_code, source_type)
        coverage_overlap = self._calculate_coverage(source_code, target_code, source_type)
        historical_compatibility = self._calculate_historical_compatibility(source_code, target_code, source_type)

        quality_score = (conceptual_similarity * 0.3 + coverage_overlap * 0.4 + historical_compatibility * 0.3)

        return min(1.0, max(0.0, quality_score))

    def _calculate_conceptual_similarity(self, source_code: str, target_code: str, source_type: str) -> float:
        """Calculate conceptual similarity between classification codes"""
        # Simplified similarity calculation based on sector descriptions
        if source_type == 'isic4':
            source_info = self.isic_rev4_sectors.get(source_code, {})
        else:
            source_info = self.isic_rev3_sectors.get(source_code, {})

        target_info = self.naics_sectors.get(target_code[:2], {})

        # Compare key terms in descriptions
        source_desc = source_info.get('description', '').lower()
        target_desc = target_info.get('description', '').lower()

        common_terms = set(source_desc.split()) & set(target_desc.split())
        total_terms = set(source_desc.split()) | set(target_desc.split())

        if len(total_terms) > 0:
            return len(common_terms) / len(total_terms)
        else:
            return 0.5  # Default similarity

    def _calculate_coverage(self, source_code: str, target_code: str, source_type: str = 'isic4') -> float:
        """Calculate coverage percentage between classification codes"""
        # Simplified coverage calculation
        # In reality, this would use detailed sub-sector mappings

        if source_type == 'isic4':
            # Check if this is a 1:1, 1:many, or many:1 mapping
            source_info = self.isic_rev4_sectors.get(source_code, {})
            naics_mapping = source_info.get('naics_mapping', [])

            if len(naics_mapping) == 1:
                return 0.9  # Good 1:1 mapping
            elif len(naics_mapping) <= 3:
                return 0.7  # Acceptable 1:many mapping
            else:
                return 0.5  # Complex mapping
        else:
            # ISIC Rev. 3 logic
            source_info = self.isic_rev3_sectors.get(source_code, {})
            naics_mapping = source_info.get('naics_mapping', [])

            if len(naics_mapping) == 1:
                return 0.8  # Good mapping
            elif len(naics_mapping) <= 2:
                return 0.6  # Acceptable mapping
            else:
                return 0.4  # Complex mapping

    def _calculate_historical_compatibility(self, source_code: str, target_code: str, source_type: str) -> float:
        """Calculate historical compatibility based on revision changes"""
        # ISIC Rev. 4 is more recent than NAICS revisions, so compatibility is generally good
        # This would in reality use detailed revision history

        if source_type == 'isic4':
            return 0.8  # Good compatibility with recent NAICS
        else:
            return 0.7  # Slightly lower compatibility for ISIC Rev. 3

    def _determine_mapping_type(self, source_code: str, target_code: str, source_type: str = 'isic4') -> str:
        """Determine the type of mapping"""
        if source_type == 'isic4':
            source_info = self.isic_rev4_sectors.get(source_code, {})
        else:
            source_info = self.isic_rev3_sectors.get(source_code, {})

        naics_mapping = source_info.get('naics_mapping', [])

        if len(naics_mapping) == 1:
            return 'One-to-One'
        elif '-' in target_code:
            return 'One-to-Many (Aggregated)'
        else:
            return 'One-to-Many'

    def _generate_mapping_comments(self, source_code: str, target_code: str, source_type: str = 'isic4') -> str:
        """Generate comments explaining the mapping"""
        comments = []

        if source_type == 'isic4':
            source_info = self.isic_rev4_sectors.get(source_code, {})
            comments.append("OECD ICIO 36-sector classification")
        else:
            source_info = self.isic_rev3_sectors.get(source_code, {})
            comments.append("WIOD 56-sector classification")

        naics_mapping = source_info.get('naics_mapping', [])
        if len(naics_mapping) > 1:
            comments.append(f"Maps to {len(naics_mapping)} NAICS categories")

        return "; ".join(comments)

    def convert_data_frame(self, df: pd.DataFrame, source_classification: str,
                          target_classification: str, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Convert data from one classification to another

        Args:
            df (pd.DataFrame): Input data frame
            source_classification (str): Source classification ('isic4', 'isic3', 'naics')
            target_classification (str): Target classification ('isic4', 'isic3', 'naics')
            column_mapping (Dict): Mapping of columns to convert

        Returns:
            pd.DataFrame: Converted data frame
        """
        logger.info(f"Converting data from {source_classification} to {target_classification}")

        # Get appropriate cross-walk
        if source_classification == 'isic4' and target_classification == 'naics':
            crosswalk = self.create_isic4_to_naics_crosswalk()
            source_col = 'ISIC4_Code'
            target_col = 'NAICS_Code'
        elif source_classification == 'isic3' and target_classification == 'naics':
            crosswalk = self.create_isic3_to_naics_crosswalk()
            source_col = 'ISIC3_Code'
            target_col = 'NAICS_Code'
        else:
            raise ValueError(f"Unsupported conversion: {source_classification} to {target_classification}")

        # Create conversion dictionary
        conversion_dict = {}
        for _, row in crosswalk.iterrows():
            conversion_dict[row[source_col]] = {
                'target_code': row[target_col],
                'quality': row['Mapping_Quality'],
                'coverage': row['Coverage_Percentage']
            }

        # Apply conversion to specified columns
        converted_df = df.copy()

        for source_col_name, target_col_name in column_mapping.items():
            if source_col_name in df.columns:
                # Map codes
                converted_df[target_col_name] = df[source_col_name].map(
                    lambda x: conversion_dict.get(x, {}).get('target_code', x)
                )

                # Add quality and coverage information
                converted_df[f'{target_col_name}_Quality'] = df[source_col_name].map(
                    lambda x: conversion_dict.get(x, {}).get('quality', 0.0)
                )
                converted_df[f'{target_col_name}_Coverage'] = df[source_col_name].map(
                    lambda x: conversion_dict.get(x, {}).get('coverage', 0.0)
                )

        logger.info(f"Data conversion completed. Output shape: {converted_df.shape}")
        return converted_df

    def get_mapping_summary(self) -> Dict[str, Union[int, float, pd.DataFrame]]:
        """
        Get summary statistics of classification mappings

        Returns:
            Dict: Mapping summary statistics
        """
        isic4_crosswalk = self.create_isic4_to_naics_crosswalk()
        isic3_crosswalk = self.create_isic3_to_naics_crosswalk()

        summary = {
            'isic4_to_naics': {
                'total_mappings': len(isic4_crosswalk),
                'unique_isic4_codes': isic4_crosswalk['ISIC4_Code'].nunique(),
                'unique_naics_codes': isic4_crosswalk['NAICS_Code'].nunique(),
                'average_quality': isic4_crosswalk['Mapping_Quality'].mean(),
                'average_coverage': isic4_crosswalk['Coverage_Percentage'].mean(),
                'high_quality_mappings': len(isic4_crosswalk[isic4_crosswalk['Mapping_Quality'] > 0.8])
            },
            'isic3_to_naics': {
                'total_mappings': len(isic3_crosswalk),
                'unique_isic3_codes': isic3_crosswalk['ISIC3_Code'].nunique(),
                'unique_naics_codes': isic3_crosswalk['NAICS_Code'].nunique(),
                'average_quality': isic3_crosswalk['Mapping_Quality'].mean(),
                'average_coverage': isic3_crosswalk['Coverage_Percentage'].mean(),
                'high_quality_mappings': len(isic3_crosswalk[isic3_crosswalk['Mapping_Quality'] > 0.8])
            },
            'crosswalk_tables': {
                'isic4_to_naics': isic4_crosswalk,
                'isic3_to_naics': isic3_crosswalk
            }
        }

        return summary

    def export_crosswalks(self, format: str = 'excel') -> bool:
        """
        Export all cross-walk tables

        Args:
            format (str): Export format ('excel', 'csv')

        Returns:
            bool: Success status
        """
        try:
            if format == 'excel':
                output_file = self.base_path / 'classification_crosswalks.xlsx'

                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    # ISIC Rev. 4 to NAICS
                    isic4_crosswalk = self.create_isic4_to_naics_crosswalk()
                    isic4_crosswalk.to_excel(writer, sheet_name='ISIC4_to_NAICS', index=False)

                    # ISIC Rev. 3 to NAICS
                    isic3_crosswalk = self.create_isic3_to_naics_crosswalk()
                    isic3_crosswalk.to_excel(writer, sheet_name='ISIC3_to_NAICS', index=False)

                    # Summary statistics
                    summary = self.get_mapping_summary()
                    summary_df = pd.DataFrame([
                        ['ISIC4 to NAICS', summary['isic4_to_naics']['total_mappings'],
                         summary['isic4_to_naics']['average_quality'], summary['isic4_to_naics']['average_coverage']],
                        ['ISIC3 to NAICS', summary['isic3_to_naics']['total_mappings'],
                         summary['isic3_to_naics']['average_quality'], summary['isic3_to_naics']['average_coverage']]
                    ], columns=['Crosswalk', 'Total Mappings', 'Average Quality', 'Average Coverage'])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

            elif format == 'csv':
                # Export individual CSV files
                isic4_crosswalk = self.create_isic4_to_naics_crosswalk()
                isic4_crosswalk.to_csv(self.base_path / 'ISIC4_to_NAICS_crosswalk.csv', index=False)

                isic3_crosswalk = self.create_isic3_to_naics_crosswalk()
                isic3_crosswalk.to_csv(self.base_path / 'ISIC3_to_NAICS_crosswalk.csv', index=False)

            logger.info(f"Cross-walk tables exported in {format} format")
            return True

        except Exception as e:
            logger.error(f"Error exporting cross-walk tables: {e}")
            return False


def main():
    """Demonstration of Classification Cross-Walk functionality"""
    print("Classification Cross-Walk Demonstration")
    print("=" * 45)

    # Initialize cross-walk system
    crosswalk = ClassificationCrossWalk()

    # Test 1: Create ISIC Rev. 4 to NAICS cross-walk
    print("\n1. Creating ISIC Rev. 4 to NAICS cross-walk...")
    isic4_crosswalk = crosswalk.create_isic4_to_naics_crosswalk()
    print(f"   Cross-walk created: {isic4_crosswalk.shape}")
    print(f"   Sample mappings:")
    print(isic4_crosswalk.head(3))

    # Test 2: Create ISIC Rev. 3 to NAICS cross-walk
    print("\n2. Creating ISIC Rev. 3 to NAICS cross-walk...")
    isic3_crosswalk = crosswalk.create_isic3_to_naics_crosswalk()
    print(f"   Cross-walk created: {isic3_crosswalk.shape}")
    print(f"   Sample mappings:")
    print(isic3_crosswalk.head(3))

    # Test 3: Get mapping summary
    print("\n3. Getting mapping summary...")
    summary = crosswalk.get_mapping_summary()
    print(f"   ISIC4 to NAICS mappings: {summary['isic4_to_naics']['total_mappings']}")
    print(f"   ISIC3 to NAICS mappings: {summary['isic3_to_naics']['total_mappings']}")
    print(f"   Average quality (ISIC4): {summary['isic4_to_naics']['average_quality']:.3f}")
    print(f"   Average quality (ISIC3): {summary['isic3_to_naics']['average_quality']:.3f}")

    # Test 4: Export cross-walks
    print("\n4. Exporting cross-walk tables...")
    success = crosswalk.export_crosswalks('excel')
    print(f"   Export {'successful' if success else 'failed'}")

    # Test 5: Sample data conversion
    print("\n5. Testing data conversion...")
    sample_data = pd.DataFrame({
        'ISIC4_Code': ['C10-C12', 'C20_C21', 'F', 'K'],
        'Value': [100, 200, 150, 300]
    })

    converted_data = crosswalk.convert_data_frame(
        sample_data, 'isic4', 'naics', {'ISIC4_Code': 'NAICS_Code'}
    )
    print(f"   Original data: {sample_data.shape}")
    print(f"   Converted data: {converted_data.shape}")
    print(f"   Converted columns: {list(converted_data.columns)}")

    print("\nClassification Cross-Walk demonstration completed!")


if __name__ == "__main__":
    main()