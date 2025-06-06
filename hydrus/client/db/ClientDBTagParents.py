import collections
import collections.abc
import itertools
import sqlite3

from hydrus.core import HydrusConstants as HC
from hydrus.core import HydrusData
from hydrus.core import HydrusDBBase

from hydrus.client.db import ClientDBDefinitionsCache
from hydrus.client.db import ClientDBMaintenance
from hydrus.client.db import ClientDBModule
from hydrus.client.db import ClientDBServices
from hydrus.client.db import ClientDBTagSiblings
from hydrus.client.metadata import ClientTags
from hydrus.client.metadata import ClientTagsHandling

def GenerateTagParentsLookupCacheTableName( display_type: int, service_id: int ):
    
    ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name ) = GenerateTagParentsLookupCacheTableNames( service_id )
    
    if display_type == ClientTags.TAG_DISPLAY_DISPLAY_IDEAL:
        
        return cache_ideal_tag_parents_lookup_table_name
        
    elif display_type == ClientTags.TAG_DISPLAY_DISPLAY_ACTUAL:
        
        return cache_actual_tag_parents_lookup_table_name
        
    

TAG_PARENTS_IDEAL_PREFIX = 'ideal_tag_parents_lookup_cache_'
TAG_PARENTS_ACTUAL_PREFIX = 'actual_tag_parents_lookup_cache_'

def GenerateTagParentsLookupCacheTableNames( service_id ):
    
    suffix = service_id
    
    cache_ideal_tag_parents_lookup_table_name = f'external_caches.{TAG_PARENTS_IDEAL_PREFIX}{suffix}'
    cache_actual_tag_parents_lookup_table_name = f'external_caches.{TAG_PARENTS_ACTUAL_PREFIX}{suffix}'
    
    return ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name )
    

TAG_PARENTS_CURRENT_STORAGE_PREFIX = 'current_tag_parents_'
TAG_PARENTS_DELETED_STORAGE_PREFIX = 'deleted_tag_parents_'
TAG_PARENTS_PENDING_STORAGE_PREFIX = 'pending_tag_parents_'
TAG_PARENTS_PETITIONED_STORAGE_PREFIX = 'petitioned_tag_parents_'

def GenerateTagParentsStorageTableNames( service_id ):
    
    suffix = service_id
    
    return {
        HC.CONTENT_STATUS_CURRENT : f'{TAG_PARENTS_CURRENT_STORAGE_PREFIX}{suffix}',
        HC.CONTENT_STATUS_DELETED : f'{TAG_PARENTS_DELETED_STORAGE_PREFIX}{suffix}',
        HC.CONTENT_STATUS_PENDING : f'{TAG_PARENTS_PENDING_STORAGE_PREFIX}{suffix}',
        HC.CONTENT_STATUS_PETITIONED : f'{TAG_PARENTS_PETITIONED_STORAGE_PREFIX}{suffix}'
    }
    

class ClientDBTagParents( ClientDBModule.ClientDBModule ):
    
    CAN_REPOPULATE_ALL_MISSING_DATA = True
    
    def __init__(
        self,
        cursor: sqlite3.Cursor,
        modules_db_maintenance: ClientDBMaintenance.ClientDBMaintenance,
        modules_services: ClientDBServices.ClientDBMasterServices,
        modules_tags_local_cache: ClientDBDefinitionsCache.ClientDBCacheLocalTags,
        modules_tag_siblings: ClientDBTagSiblings.ClientDBTagSiblings
    ):
        
        self.modules_db_maintenance = modules_db_maintenance
        self.modules_services = modules_services
        self.modules_tags_local_cache = modules_tags_local_cache
        self.modules_tag_siblings = modules_tag_siblings
        
        self._service_ids_to_display_application_status = {}
        
        self._service_ids_to_applicable_service_ids = None
        self._service_ids_to_interested_service_ids = None
        
        super().__init__( 'client tag parents', cursor )
        
    
    def _GetInitialIndexGenerationDict( self ) -> dict:
        
        index_generation_dict = {}
        
        return index_generation_dict
        
    
    def _GetInitialTableGenerationDict( self ) -> dict:
        
        return {
            'main.tag_parent_application' : ( 'CREATE TABLE IF NOT EXISTS {} ( master_service_id INTEGER, service_index INTEGER, application_service_id INTEGER, PRIMARY KEY ( master_service_id, service_index ) );', 414 )
        }
        
    
    def _GetServiceIndexGenerationDict( self, service_id ) -> dict:
        
        ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name ) = GenerateTagParentsLookupCacheTableNames( service_id )
        
        index_generation_dict = {}
        
        index_generation_dict[ cache_actual_tag_parents_lookup_table_name ] = [
            ( [ 'ancestor_tag_id' ], False, 414 )
        ]
        
        index_generation_dict[ cache_ideal_tag_parents_lookup_table_name ] = [
            ( [ 'ancestor_tag_id' ], False, 414 )
        ]
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        index_generation_dict[ statuses_to_storage_table_names[ HC.CONTENT_STATUS_CURRENT ] ] = [
            ( [ 'parent_tag_id' ], False, 586 )
        ]
        
        index_generation_dict[ statuses_to_storage_table_names[ HC.CONTENT_STATUS_DELETED ] ] = [
            ( [ 'parent_tag_id' ], False, 586 )
        ]
        
        index_generation_dict[ statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ] ] = [
            ( [ 'parent_tag_id' ], False, 586 )
        ]
        
        index_generation_dict[ statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ] ] = [
            ( [ 'parent_tag_id' ], False, 586 )
        ]
        
        return index_generation_dict
        
    
    def _GetServiceTableGenerationDict( self, service_id ) -> dict:
        
        ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name ) = GenerateTagParentsLookupCacheTableNames( service_id )
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        return {
            cache_actual_tag_parents_lookup_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, ancestor_tag_id INTEGER, PRIMARY KEY ( child_tag_id, ancestor_tag_id ) );', 414 ),
            cache_ideal_tag_parents_lookup_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, ancestor_tag_id INTEGER, PRIMARY KEY ( child_tag_id, ancestor_tag_id ) );', 414 ),
            statuses_to_storage_table_names[ HC.CONTENT_STATUS_CURRENT ] : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, parent_tag_id INTEGER, PRIMARY KEY ( child_tag_id, parent_tag_id ) );', 586 ),
            statuses_to_storage_table_names[ HC.CONTENT_STATUS_DELETED ] : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, parent_tag_id INTEGER, PRIMARY KEY ( child_tag_id, parent_tag_id ) );', 586 ),
            statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ] : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, parent_tag_id INTEGER, reason_id INTEGER, PRIMARY KEY ( child_tag_id, parent_tag_id ) );', 586 ),
            statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ] : ( 'CREATE TABLE IF NOT EXISTS {} ( child_tag_id INTEGER, parent_tag_id INTEGER, reason_id INTEGER, PRIMARY KEY ( child_tag_id, parent_tag_id ) );', 586 )
        }
        
    
    def _GetServiceTablePrefixes( self ):
        
        return {
            TAG_PARENTS_IDEAL_PREFIX,
            TAG_PARENTS_ACTUAL_PREFIX,
            TAG_PARENTS_CURRENT_STORAGE_PREFIX,
            TAG_PARENTS_DELETED_STORAGE_PREFIX,
            TAG_PARENTS_PENDING_STORAGE_PREFIX,
            TAG_PARENTS_PETITIONED_STORAGE_PREFIX
        }
        
    
    def _GetServiceIdsWeGenerateDynamicTablesFor( self ):
        
        return self.modules_services.GetServiceIds( HC.REAL_TAG_SERVICES )
        
    
    def _RepairRepopulateTables( self, repopulate_table_names, cursor_transaction_wrapper: HydrusDBBase.DBCursorTransactionWrapper ):
        
        for service_id in self._GetServiceIdsWeGenerateDynamicTablesFor():
            
            table_generation_dict = self._GetServiceTableGenerationDict( service_id )
            
            this_service_table_names = set( table_generation_dict.keys() )
            
            this_service_needs_repopulation = len( this_service_table_names.intersection( repopulate_table_names ) ) > 0
            
            if this_service_needs_repopulation:
                
                self._service_ids_to_applicable_service_ids = None
                self._service_ids_to_interested_service_ids = None
                
                self.Regen( ( service_id, ) )
                
                cursor_transaction_wrapper.CommitAndBegin()
                
            
        
    
    def AddTagParents( self, service_id, pairs ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[HC.CONTENT_STATUS_DELETED]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[HC.CONTENT_STATUS_PENDING]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        
        self._ExecuteMany( f'INSERT OR IGNORE INTO {statuses_to_storage_table_names[HC.CONTENT_STATUS_CURRENT]} ( child_tag_id, parent_tag_id ) VALUES ( ?, ? );', pairs )
        
    
    def ClearActual( self, service_id, tag_ids = None ):
        
        cache_actual_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( ClientTags.TAG_DISPLAY_DISPLAY_ACTUAL, service_id )
        
        if tag_ids is None:
            
            self._Execute( 'DELETE FROM {};'.format( cache_actual_tag_parents_lookup_table_name ) )
            
        else:
            
            self._ExecuteMany( f'DELETE FROM {cache_actual_tag_parents_lookup_table_name} WHERE child_tag_id = ? OR ancestor_tag_id = ?;', ( ( tag_id, tag_id ) for tag_id in tag_ids ) )
            
        
        if service_id in self._service_ids_to_display_application_status:
            
            del self._service_ids_to_display_application_status[ service_id ]
            
        
    
    def DeletePending( self, service_id ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._Execute( f'DELETE FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ]};' )
        self._Execute( f'DELETE FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ]};' )
        
    
    def DeleteTagParents( self, service_id, pairs ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[HC.CONTENT_STATUS_CURRENT]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[HC.CONTENT_STATUS_PETITIONED]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        
        self._ExecuteMany( f'INSERT OR IGNORE INTO {statuses_to_storage_table_names[HC.CONTENT_STATUS_DELETED]} ( child_tag_id, parent_tag_id ) VALUES ( ?, ? );', pairs )
        
    
    def Drop( self, tag_service_id ):
        
        for table_name in GenerateTagParentsStorageTableNames( tag_service_id ).values():
            
            self.modules_db_maintenance.DeferredDropTable( table_name )
            
        
        ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name ) = GenerateTagParentsLookupCacheTableNames( tag_service_id )
        
        self.modules_db_maintenance.DeferredDropTable( cache_actual_tag_parents_lookup_table_name )
        self.modules_db_maintenance.DeferredDropTable( cache_ideal_tag_parents_lookup_table_name )
        
        self._Execute( 'DELETE FROM tag_parent_application WHERE master_service_id = ? OR application_service_id = ?;', ( tag_service_id, tag_service_id ) )
        
        self._service_ids_to_applicable_service_ids = None
        self._service_ids_to_interested_service_ids = None
        
    
    def FilterChained( self, display_type, tag_service_id, ideal_tag_ids ):
        
        if len( ideal_tag_ids ) == 0:
            
            return set()
            
        elif len( ideal_tag_ids ) == 1:
            
            ( ideal_tag_id, ) = ideal_tag_ids
            
            if self.IsChained( display_type, tag_service_id, ideal_tag_id ):
                
                return { ideal_tag_id }
                
            else:
                
                return set()
                
            
        
        # get the tag_ids that are part of a parent chain
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        with self._MakeTemporaryIntegerTable( ideal_tag_ids, 'tag_id' ) as temp_table_name:
            
            # keep these separate--older sqlite can't do cross join to an OR ON
            
            # temp tags to lookup
            chain_tag_ids = self._STS( self._Execute( 'SELECT tag_id FROM {} CROSS JOIN {} ON ( child_tag_id = tag_id );'.format( temp_table_name, cache_tag_parents_lookup_table_name ) ) )
            chain_tag_ids.update( self._STI( self._Execute( 'SELECT tag_id FROM {} CROSS JOIN {} ON ( ancestor_tag_id = tag_id );'.format( temp_table_name, cache_tag_parents_lookup_table_name ) ) ) )
            
        
        return chain_tag_ids
        
    
    def Generate( self, tag_service_id ):
        
        table_generation_dict = self._GetServiceTableGenerationDict( tag_service_id )
        
        for ( table_name, ( create_query_without_name, version_added ) ) in table_generation_dict.items():
            
            self._CreateTable( create_query_without_name, table_name )
            
        
        index_generation_dict = self._GetServiceIndexGenerationDict( tag_service_id )
        
        for ( table_name, columns, unique, version_added ) in self._FlattenIndexGenerationDict( index_generation_dict ):
            
            self._CreateIndex( table_name, columns, unique = unique )
            
        
        self._Execute( 'INSERT OR IGNORE INTO tag_parent_application ( master_service_id, service_index, application_service_id ) VALUES ( ?, ?, ? );', ( tag_service_id, 0, tag_service_id ) )
        
        self._service_ids_to_applicable_service_ids = None
        self._service_ids_to_interested_service_ids = None
        
        self.Regen( ( tag_service_id, ) )
        
    
    def GenerateApplicationDicts( self ):
        
        unsorted_dict = HydrusData.BuildKeyToListDict( ( master_service_id, ( index, application_service_id ) ) for ( master_service_id, index, application_service_id ) in self._Execute( 'SELECT master_service_id, service_index, application_service_id FROM tag_parent_application;' ) )
        
        self._service_ids_to_applicable_service_ids = collections.defaultdict( list )
        
        self._service_ids_to_applicable_service_ids.update( { master_service_id : [ application_service_id for ( index, application_service_id ) in sorted( index_and_applicable_service_ids ) ] for ( master_service_id, index_and_applicable_service_ids ) in unsorted_dict.items() } )
        
        self._service_ids_to_interested_service_ids = collections.defaultdict( set )
        
        for ( master_service_id, application_service_ids ) in self._service_ids_to_applicable_service_ids.items():
            
            for application_service_id in application_service_ids:
                
                self._service_ids_to_interested_service_ids[ application_service_id ].add( master_service_id )
                
            
        
    
    def GetAllTagIds( self, display_type, tag_service_id ):
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        tag_ids = set()
        
        tag_ids.update( self._STI( self._Execute( 'SELECT DISTINCT child_tag_id FROM {};'.format( cache_tag_parents_lookup_table_name ) ) ) )
        tag_ids.update( self._STI( self._Execute( 'SELECT DISTINCT ancestor_tag_id FROM {};'.format( cache_tag_parents_lookup_table_name ) ) ) )
        
        return tag_ids
        
    
    def GetAncestors( self, display_type: int, tag_service_id: int, ideal_tag_id: int ):
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        ancestor_ids = self._STS( self._Execute( 'SELECT ancestor_tag_id FROM {} WHERE child_tag_id = ?;'.format( cache_tag_parents_lookup_table_name ), ( ideal_tag_id, ) ) )
        
        return ancestor_ids
        
    
    def GetApplicableServiceIds( self, tag_service_id ):
        
        if self._service_ids_to_applicable_service_ids is None:
            
            self.GenerateApplicationDicts()
            
        
        return self._service_ids_to_applicable_service_ids[ tag_service_id ]
        
    
    def GetApplication( self ):
        
        if self._service_ids_to_applicable_service_ids is None:
            
            self.GenerateApplicationDicts()
            
        
        service_ids_to_service_keys = {}
        
        service_keys_to_parent_applicable_service_keys = {}
        
        for ( master_service_id, applicable_service_ids ) in self._service_ids_to_applicable_service_ids.items():
            
            all_service_ids = [ master_service_id ] + list( applicable_service_ids )
            
            for service_id in all_service_ids:
                
                if service_id not in service_ids_to_service_keys:
                    
                    service_ids_to_service_keys[ service_id ] = self.modules_services.GetService( service_id ).GetServiceKey()
                    
                
            
            service_keys_to_parent_applicable_service_keys[ service_ids_to_service_keys[ master_service_id ] ] = [ service_ids_to_service_keys[ service_id ] for service_id in applicable_service_ids ]
            
        
        return service_keys_to_parent_applicable_service_keys
        
    
    def GetApplicationStatus( self, service_id ):
        
        if service_id not in self._service_ids_to_display_application_status:
            
            ( cache_ideal_tag_parents_lookup_table_name, cache_actual_tag_parents_lookup_table_name ) = GenerateTagParentsLookupCacheTableNames( service_id )
            
            actual_parent_rows = set( self._Execute( 'SELECT child_tag_id, ancestor_tag_id FROM {};'.format( cache_actual_tag_parents_lookup_table_name ) ) )
            ideal_parent_rows = set( self._Execute( 'SELECT child_tag_id, ancestor_tag_id FROM {};'.format( cache_ideal_tag_parents_lookup_table_name ) ) )
            
            parent_rows_to_remove = actual_parent_rows.difference( ideal_parent_rows )
            parent_rows_to_add = ideal_parent_rows.difference( actual_parent_rows )
            
            self._service_ids_to_display_application_status[ service_id ] = ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove )
            
        
        ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove ) = self._service_ids_to_display_application_status[ service_id ]
        
        return ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove )
        
    
    def GetChainsMembers( self, display_type: int, tag_service_id: int, ideal_tag_ids: collections.abc.Collection[ int ] ):
        
        if len( ideal_tag_ids ) == 0:
            
            return set()
            
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        chain_tag_ids = set( ideal_tag_ids )
        we_have_looked_up = set()
        next_search_tag_ids = set( ideal_tag_ids )
        
        while len( next_search_tag_ids ) > 0:
            
            if len( next_search_tag_ids ) == 1:
                
                ( ideal_tag_id, ) = next_search_tag_ids
                
                round_of_tag_ids = self._STS( self._Execute( f'SELECT child_tag_id FROM {cache_tag_parents_lookup_table_name} WHERE ancestor_tag_id = ?;', ( ideal_tag_id, ) ) )
                round_of_tag_ids.update( self._STI( self._Execute( f'SELECT ancestor_tag_id FROM {cache_tag_parents_lookup_table_name} WHERE child_tag_id = ?;', ( ideal_tag_id, ) ) ) )
                
            else:
                
                with self._MakeTemporaryIntegerTable( next_search_tag_ids, 'tag_id' ) as temp_next_search_tag_ids_table_name:
                    
                    round_of_tag_ids = self._STS( self._Execute( f'SELECT child_tag_id FROM {temp_next_search_tag_ids_table_name} CROSS JOIN {cache_tag_parents_lookup_table_name} ON ( ancestor_tag_id = tag_id );' ) )
                    round_of_tag_ids.update( self._STI( self._Execute( f' SELECT ancestor_tag_id FROM {temp_next_search_tag_ids_table_name} CROSS JOIN {cache_tag_parents_lookup_table_name} ON ( child_tag_id = tag_id );' ) ) )
                    
                
            
            chain_tag_ids.update( round_of_tag_ids )
            
            we_have_looked_up.update( next_search_tag_ids )
            
            next_search_tag_ids = round_of_tag_ids.difference( we_have_looked_up )
            
        
        return chain_tag_ids
        
    
    def GetChainsMembersTables( self, display_type: int, tag_service_id: int, ideal_tag_ids_table_name: str, results_table_name: str ):
        
        raise NotImplementedError()
        
        # if it isn't crazy, I should write this whole lad to be one or two recursive queries
        # also ditch the UNION if we get that far
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        first_ideal_tag_ids = self._STS( self._Execute( 'SELECT ideal_tag_id FROM {};'.format( ideal_tag_ids_table_name ) ) )
        
        chain_tag_ids = set( first_ideal_tag_ids )
        we_have_looked_up = set()
        next_search_tag_ids = set( first_ideal_tag_ids )
        
        while len( next_search_tag_ids ) > 0:
            
            if len( next_search_tag_ids ) == 1:
                
                ( ideal_tag_id, ) = next_search_tag_ids
                
                round_of_tag_ids = self._STS( self._Execute( 'SELECT child_tag_id FROM {} WHERE ancestor_tag_id = ? UNION ALL SELECT ancestor_tag_id FROM {} WHERE child_tag_id = ?;'.format( cache_tag_parents_lookup_table_name, cache_tag_parents_lookup_table_name ), ( ideal_tag_id, ideal_tag_id ) ) )
                
            else:
                
                with self._MakeTemporaryIntegerTable( next_search_tag_ids, 'tag_id' ) as temp_next_search_tag_ids_table_name:
                    
                    round_of_tag_ids = self._STS( self._Execute( 'SELECT child_tag_id FROM {} CROSS JOIN {} ON ( ancestor_tag_id = tag_id ) UNION ALL SELECT ancestor_tag_id FROM {} CROSS JOIN {} ON ( child_tag_id = tag_id );'.format( temp_next_search_tag_ids_table_name, cache_tag_parents_lookup_table_name, temp_next_search_tag_ids_table_name, cache_tag_parents_lookup_table_name ) ) )
                    
                
            
            new_tag_ids = round_of_tag_ids.difference( chain_tag_ids )
            
            if len( new_tag_ids ) > 0:
                
                self._ExecuteMany( 'INSERT OR IGNORE INTO {} ( tag_id ) VALUES ( ? );', ( ( tag_id, ) for tag_id in round_of_tag_ids.difference( new_tag_ids ) ) )
                
                chain_tag_ids.update( new_tag_ids )
                
            
            we_have_looked_up.update( next_search_tag_ids )
            
            next_search_tag_ids = round_of_tag_ids.difference( we_have_looked_up )
            
        
    
    def GetDescendants( self, display_type: int, tag_service_id: int, ideal_tag_id: int ):
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        descendant_ids = self._STS( self._Execute( 'SELECT child_tag_id FROM {} WHERE ancestor_tag_id = ?;'.format( cache_tag_parents_lookup_table_name ), ( ideal_tag_id, ) ) )
        
        return descendant_ids
        
    
    def GetInterestedServiceIds( self, tag_service_id ):
        
        if self._service_ids_to_interested_service_ids is None:
            
            self.GenerateApplicationDicts()
            
        
        return self._service_ids_to_interested_service_ids[ tag_service_id ]
        
    
    def GetPendingParentsCount( self, service_id: int ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        ( info, ) = self._Execute( f'SELECT COUNT( * ) FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ]};' ).fetchone()
        
        return info
        
    
    def GetPetitionedParentsCount( self, service_id: int ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        ( info, ) = self._Execute( f'SELECT COUNT( * ) FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ]};' ).fetchone()
        
        return info
        
    
    def GetTablesAndColumnsThatUseDefinitions( self, content_type: int ) -> list[ tuple[ str, str ] ]:
        
        tables_and_columns = []
        
        if content_type == HC.CONTENT_TYPE_TAG:
            
            for service_id in self._GetServiceIdsWeGenerateDynamicTablesFor():
                
                for table_name in GenerateTagParentsStorageTableNames( service_id ).values():
                    
                    tables_and_columns.append( ( table_name, 'child_tag_id' ) )
                    tables_and_columns.append( ( table_name, 'parent_tag_id' ) )
                    
                
                for table_name in GenerateTagParentsLookupCacheTableNames( service_id ):
                    
                    tables_and_columns.append( ( table_name, 'child_tag_id' ) )
                    tables_and_columns.append( ( table_name, 'ancestor_tag_id' ) )
                    
                
            
        
        return tables_and_columns
        
    
    def GetTagParents( self, service_key, tags = None, where_chain_includes_pending_or_petitioned = False ):
        
        service_id = self.modules_services.GetServiceId( service_key )
        
        if tags is None and not where_chain_includes_pending_or_petitioned:
            
            statuses_to_pair_ids = self.GetTagParentsIds( service_id )
            
        else:
            
            if where_chain_includes_pending_or_petitioned:
                
                tag_ids = set()
                
                statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
                
                queries = [
                    f'SELECT child_tag_id, parent_tag_id FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ]};',
                    f'SELECT child_tag_id, parent_tag_id FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ]};'
                ]
                
                for query in queries:
                    
                    for pair in self._Execute( query ):
                        
                        tag_ids.update( pair )
                        
                    
                
            else:
                
                tag_ids = set( self.modules_tags_local_cache.GetTagIdsToTags( tags = tags ).keys() )
                
            
            statuses_to_pair_ids = self.GetTagParentsIdsChains( service_id, tag_ids )
            
        
        all_tag_ids = set()
        
        for pair_ids in statuses_to_pair_ids.values():
            
            for ( child_tag_id, parent_tag_id ) in pair_ids:
                
                all_tag_ids.add( child_tag_id )
                all_tag_ids.add( parent_tag_id )
                
            
        
        tag_ids_to_tags = self.modules_tags_local_cache.GetTagIdsToTags( tag_ids = all_tag_ids )
        
        statuses_to_pairs = collections.defaultdict( set )
        
        statuses_to_pairs.update( { status : { ( tag_ids_to_tags[ child_tag_id ], tag_ids_to_tags[ parent_tag_id ] ) for ( child_tag_id, parent_tag_id ) in pair_ids } for ( status, pair_ids ) in statuses_to_pair_ids.items() } )
        
        return statuses_to_pairs
        
    
    def GetTagParentsIds( self, service_id ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        statuses_to_pair_ids = collections.defaultdict( list )
        
        for ( status, table_name ) in statuses_to_storage_table_names.items():
            
            statuses_to_pair_ids[ status ] = sorted( self._Execute( f'SELECT child_tag_id, parent_tag_id FROM {table_name};' ).fetchall() )
            
        
        return statuses_to_pair_ids
        
    
    def GetTagParentsIdsChains( self, service_id, tag_ids ):
        
        # I experimented with one or two recursive queries, and for siblings, but it mostly ended up hellmode index efficiency. I think ( service_id, integer ) did it in
        
        # note that this has to do sibling lookup as well to fetch pairs that are only connected to our chain by sibling relationships, and we are assuming here that the sibling lookup cache is valid
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        searched_tag_ids = set()
        next_tag_ids = set( tag_ids )
        
        unsorted_statuses_to_pair_ids = collections.defaultdict( set )
        
        while len( next_tag_ids ) > 0:
            
            this_loop_tag_ids = set( next_tag_ids )
            
            next_tag_ids = set()
            
            ideal_tag_ids = self.modules_tag_siblings.GetIdealTagIds( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, service_id, this_loop_tag_ids )
            
            this_loop_tag_ids.update( self.modules_tag_siblings.GetChainsMembersFromIdeals( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, service_id, ideal_tag_ids ) )
            
            # I _think_ this is always a no-op?
            this_loop_tag_ids.difference_update( searched_tag_ids )
            
            with self._MakeTemporaryIntegerTable( this_loop_tag_ids, 'tag_id' ) as temp_this_loop_tag_ids_table_name:
                
                # keep these separate--older sqlite can't do cross join to an OR ON
                # ALSO ditching UNION, which perhaps was not helping!
                
                # just a note, this thing is inefficient--it fetches the same rows twice, looking from either direction
                # there's probably a way to more carefully shape the iterations of search, remembering which direction we got things from or something, but it wouldn't be trivial I think!
                
                for ( status, table_name ) in statuses_to_storage_table_names.items():
                    
                    queries = [
                        f'SELECT child_tag_id, parent_tag_id FROM {temp_this_loop_tag_ids_table_name} CROSS JOIN {table_name} ON ( child_tag_id = tag_id );',
                        f'SELECT child_tag_id, parent_tag_id FROM {temp_this_loop_tag_ids_table_name} CROSS JOIN {table_name} ON ( parent_tag_id = tag_id );'
                    ]
                    
                    for query in queries:
                        
                        for pair in self._Execute( query ):
                            
                            unsorted_statuses_to_pair_ids[ status ].add( pair )
                            
                            next_tag_ids.update( pair )
                            
                        
                    
                
            
            searched_tag_ids.update( this_loop_tag_ids )
            
            next_tag_ids.difference_update( searched_tag_ids )
            
        
        statuses_to_pair_ids = collections.defaultdict( list )
        
        statuses_to_pair_ids.update( { status : sorted( pair_ids ) for ( status, pair_ids ) in unsorted_statuses_to_pair_ids.items() } )
        
        return statuses_to_pair_ids
        
    
    def GetTagsToAncestors( self, display_type: int, tag_service_id: int, ideal_tag_ids: collections.abc.Collection[ int ] ):
        
        if len( ideal_tag_ids ) == 0:
            
            return {}
            
        elif len( ideal_tag_ids ) == 1:
            
            ( ideal_tag_id, ) = ideal_tag_ids
            
            ancestors = self.GetAncestors( display_type, tag_service_id, ideal_tag_id )
            
            return { ideal_tag_id : ancestors }
            
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        with self._MakeTemporaryIntegerTable( ideal_tag_ids, 'child_tag_id' ) as temp_table_name:
            
            tag_ids_to_ancestors = HydrusData.BuildKeyToSetDict( self._Execute( 'SELECT child_tag_id, ancestor_tag_id FROM {} CROSS JOIN {} USING ( child_tag_id );'.format( temp_table_name, cache_tag_parents_lookup_table_name ) ) )
            
        
        for tag_id in ideal_tag_ids:
            
            if tag_id not in tag_ids_to_ancestors:
                
                tag_ids_to_ancestors[ tag_id ] = set()
                
            
        
        return tag_ids_to_ancestors
        
    
    def GetTagsToDescendants( self, display_type: int, tag_service_id: int, ideal_tag_ids: collections.abc.Collection[ int ] ):
        
        if len( ideal_tag_ids ) == 0:
            
            return {}
            
        elif len( ideal_tag_ids ) == 1:
            
            ( ideal_tag_id, ) = ideal_tag_ids
            
            descendants = self.GetDescendants( display_type, tag_service_id, ideal_tag_id )
            
            return { ideal_tag_id : descendants }
            
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        with self._MakeTemporaryIntegerTable( ideal_tag_ids, 'ancestor_tag_id' ) as temp_table_name:
            
            tag_ids_to_descendants = HydrusData.BuildKeyToSetDict( self._Execute( 'SELECT ancestor_tag_id, child_tag_id FROM {} CROSS JOIN {} USING ( ancestor_tag_id );'.format( temp_table_name, cache_tag_parents_lookup_table_name ) ) )
            
        
        for ideal_tag_id in ideal_tag_ids:
            
            if ideal_tag_id not in tag_ids_to_descendants:
                
                tag_ids_to_descendants[ ideal_tag_id ] = set()
                
            
        
        return tag_ids_to_descendants
        
    
    def IdealiseStatusesToPairIds( self, tag_service_id, unideal_statuses_to_pair_ids ):
        
        all_tag_ids = set( itertools.chain.from_iterable( ( itertools.chain.from_iterable( pair_ids ) for pair_ids in unideal_statuses_to_pair_ids.values() ) ) )
        
        tag_ids_to_ideal_tag_ids = self.modules_tag_siblings.GetTagIdsToIdealTagIds( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id, all_tag_ids )
        
        ideal_statuses_to_pair_ids = collections.defaultdict( list )
        
        for ( status, pair_ids ) in unideal_statuses_to_pair_ids.items():
            
            ideal_pair_ids = sorted( ( ( tag_ids_to_ideal_tag_ids[ child_tag_id ], tag_ids_to_ideal_tag_ids[ parent_tag_id ] ) for ( child_tag_id, parent_tag_id ) in pair_ids ) )
            
            ideal_statuses_to_pair_ids[ status ] = ideal_pair_ids
            
        
        return ideal_statuses_to_pair_ids
        
    
    def IsChained( self, display_type, tag_service_id, ideal_tag_id ):
        
        cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( display_type, tag_service_id )
        
        return self._Execute( 'SELECT 1 FROM {} WHERE child_tag_id = ? OR ancestor_tag_id = ?;'.format( cache_tag_parents_lookup_table_name ), ( ideal_tag_id, ideal_tag_id ) ).fetchone() is not None
        
    
    def NotifyParentAddRowSynced( self, tag_service_id, row ):
        
        if tag_service_id in self._service_ids_to_display_application_status:
            
            ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove ) = self._service_ids_to_display_application_status[ tag_service_id ]
            
            actual_parent_rows.add( row )
            parent_rows_to_add.discard( row )
            
            self._service_ids_to_display_application_status[ tag_service_id ] = ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove )
            
        
    
    def NotifyParentDeleteRowSynced( self, tag_service_id, row ):
        
        if tag_service_id in self._service_ids_to_display_application_status:
            
            ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove ) = self._service_ids_to_display_application_status[ tag_service_id ]
            
            actual_parent_rows.discard( row )
            parent_rows_to_remove.discard( row )
            
            self._service_ids_to_display_application_status[ tag_service_id ] = ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove )
            
        
    
    def PendTagParents( self, service_id, triples ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'REPLACE INTO {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ]} ( child_tag_id, parent_tag_id, reason_id ) VALUES ( ?, ?, ? );', triples )
        
    
    def PetitionTagParents( self, service_id, triples ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'REPLACE INTO {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ]} ( child_tag_id, parent_tag_id, reason_id ) VALUES ( ?, ?, ? );', triples )
        
    
    def RescindPendingTagParents( self, service_id, pairs ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PENDING ]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        
    
    def RescindPetitionedTagParents( self, service_id, pairs ):
        
        statuses_to_storage_table_names = GenerateTagParentsStorageTableNames( service_id )
        
        self._ExecuteMany( f'DELETE FROM {statuses_to_storage_table_names[ HC.CONTENT_STATUS_PETITIONED ]} WHERE child_tag_id = ? AND parent_tag_id = ?;', pairs )
        
    
    def Regen( self, tag_service_ids ):
        
        for tag_service_id in tag_service_ids:
            
            cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id )
            
            self._Execute( 'DELETE FROM {};'.format( cache_tag_parents_lookup_table_name ) )
            
            applicable_service_ids = self.GetApplicableServiceIds( tag_service_id )
            
            tps = ClientTagsHandling.TagParentsStructure()
            
            for applicable_service_id in applicable_service_ids:
                
                unideal_statuses_to_pair_ids = self.GetTagParentsIds( service_id = applicable_service_id )
                
                # we have to collapse the parent ids according to siblings
                
                ideal_statuses_to_pair_ids = self.IdealiseStatusesToPairIds( tag_service_id, unideal_statuses_to_pair_ids )
                
                #
                
                petitioned_fast_lookup = set( ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_PETITIONED ] )
                
                for ( child_tag_id, parent_tag_id ) in ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_CURRENT ]:
                    
                    if ( child_tag_id, parent_tag_id ) in petitioned_fast_lookup:
                        
                        continue
                        
                    
                    tps.AddPair( child_tag_id, parent_tag_id )
                    
                
                for ( child_tag_id, parent_tag_id ) in ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_PENDING ]:
                    
                    tps.AddPair( child_tag_id, parent_tag_id )
                    
                
            
            self._ExecuteMany( 'INSERT OR IGNORE INTO {} ( child_tag_id, ancestor_tag_id ) VALUES ( ?, ? );'.format( cache_tag_parents_lookup_table_name ), tps.IterateDescendantAncestorPairs() )
            
            if tag_service_id in self._service_ids_to_display_application_status:
                
                del self._service_ids_to_display_application_status[ tag_service_id ]
                
            
        
    
    def RegenChains( self, tag_service_ids, tag_ids ):
        
        if self._service_ids_to_applicable_service_ids is None:
            
            self.GenerateApplicationDicts()
            
        
        if len( tag_ids ) == 0:
            
            return
            
        
        for tag_service_id in tag_service_ids:
            
            cache_tag_parents_lookup_table_name = GenerateTagParentsLookupCacheTableName( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id )
            
            # it is possible that the parents cache currently contains non-ideal tag_ids
            # so, to be safe, we'll also get all sibling chain members
            
            tag_ids_to_clear_and_regen = set( tag_ids )
            
            ideal_tag_ids = self.modules_tag_siblings.GetIdealTagIds( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id, tag_ids )
            
            tag_ids_to_clear_and_regen.update( self.modules_tag_siblings.GetChainsMembersFromIdeals( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id, ideal_tag_ids ) )
            
            # and now all possible current parent chains based on this
            
            tag_ids_to_clear_and_regen.update( self.GetChainsMembers( ClientTags.TAG_DISPLAY_DISPLAY_IDEAL, tag_service_id, tag_ids_to_clear_and_regen ) )
            
            # this should now contain all possible tag_ids that could be in tag parents right now related to what we were given
            
            if tag_service_id in self._service_ids_to_applicable_service_ids:
                
                with self._MakeTemporaryIntegerTable( tag_ids_to_clear_and_regen, 'tag_id' ) as temp_tag_ids_table_name:
                    
                    stuff_deleted = set( self._Execute( f'SELECT child_tag_id, ancestor_tag_id FROM {temp_tag_ids_table_name} CROSS JOIN {cache_tag_parents_lookup_table_name} ON ( child_tag_id = tag_id );' ) )
                    stuff_deleted.update( self._Execute( f'SELECT child_tag_id, ancestor_tag_id FROM {temp_tag_ids_table_name} CROSS JOIN {cache_tag_parents_lookup_table_name} ON ( ancestor_tag_id = tag_id );' ) )
                    
                
            else:
                
                stuff_deleted = set()
                
            
            self._ExecuteMany( 'DELETE FROM {} WHERE child_tag_id = ? OR ancestor_tag_id = ?;'.format( cache_tag_parents_lookup_table_name ), ( ( tag_id, tag_id ) for tag_id in tag_ids_to_clear_and_regen ) )
            
            # we wipe them
            
            applicable_tag_service_ids = self.GetApplicableServiceIds( tag_service_id )
            
            tps = ClientTagsHandling.TagParentsStructure()
            
            for applicable_tag_service_id in applicable_tag_service_ids:
                
                unideal_statuses_to_pair_ids = self.GetTagParentsIdsChains( applicable_tag_service_id, tag_ids_to_clear_and_regen )
                
                ideal_statuses_to_pair_ids = self.IdealiseStatusesToPairIds( tag_service_id, unideal_statuses_to_pair_ids )
                
                #
                
                petitioned_fast_lookup = set( ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_PETITIONED ] )
                
                for ( child_tag_id, parent_tag_id ) in ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_CURRENT ]:
                    
                    if ( child_tag_id, parent_tag_id ) in petitioned_fast_lookup:
                        
                        continue
                        
                    
                    tps.AddPair( child_tag_id, parent_tag_id )
                    
                
                for ( child_tag_id, parent_tag_id ) in ideal_statuses_to_pair_ids[ HC.CONTENT_STATUS_PENDING ]:
                    
                    tps.AddPair( child_tag_id, parent_tag_id )
                    
                
            
            stuff_added = set( tps.IterateDescendantAncestorPairs() )
            
            self._ExecuteMany( 'INSERT OR IGNORE INTO {} ( child_tag_id, ancestor_tag_id ) VALUES ( ?, ? );'.format( cache_tag_parents_lookup_table_name ), stuff_added )
            
            if tag_service_id in self._service_ids_to_display_application_status:
                
                stuff_no_changes = stuff_deleted.intersection( stuff_added )
                stuff_deleted.difference_update( stuff_no_changes )
                stuff_added.difference_update( stuff_no_changes )
                
                ( actual_parent_rows, ideal_parent_rows, parent_rows_to_add, parent_rows_to_remove ) = self._service_ids_to_display_application_status[ tag_service_id ]
                
                ideal_parent_rows.difference_update( stuff_deleted )
                parent_rows_to_add.difference_update( stuff_deleted )
                parent_rows_to_remove.update( actual_parent_rows.intersection( stuff_deleted ) )
                
                ideal_parent_rows.update( stuff_added )
                parent_rows_to_add.update( stuff_added.difference( actual_parent_rows ) )
                parent_rows_to_remove.difference_update( stuff_added )
                
            
        
    
    def SetApplication( self, service_keys_to_applicable_service_keys ):
        
        if self._service_ids_to_applicable_service_ids is None:
            
            self.GenerateApplicationDicts()
            
        
        new_service_ids_to_applicable_service_ids = collections.defaultdict( list )
        
        for ( master_service_key, applicable_service_keys ) in service_keys_to_applicable_service_keys.items():
            
            master_service_id = self.modules_services.GetServiceId( master_service_key )
            applicable_service_ids = [ self.modules_services.GetServiceId( service_key ) for service_key in applicable_service_keys ]
            
            new_service_ids_to_applicable_service_ids[ master_service_id ] = applicable_service_ids
            
        
        old_and_new_master_service_ids = set( self._service_ids_to_applicable_service_ids.keys() )
        old_and_new_master_service_ids.update( new_service_ids_to_applicable_service_ids.keys() )
        
        inserts = []
        
        service_ids_to_sync = set()
        
        for master_service_id in old_and_new_master_service_ids:
            
            if master_service_id in new_service_ids_to_applicable_service_ids:
                
                applicable_service_ids = new_service_ids_to_applicable_service_ids[ master_service_id ]
                
                inserts.extend( ( ( master_service_id, i, applicable_service_id ) for ( i, applicable_service_id ) in enumerate( applicable_service_ids ) ) )
                
                if applicable_service_ids != self._service_ids_to_applicable_service_ids[ master_service_id ]:
                    
                    service_ids_to_sync.add( master_service_id )
                    
                
            else:
                
                service_ids_to_sync.add( master_service_id )
                
            
        
        self._Execute( 'DELETE FROM tag_parent_application;' )
        
        self._ExecuteMany( 'INSERT OR IGNORE INTO tag_parent_application ( master_service_id, service_index, application_service_id ) VALUES ( ?, ?, ? );', inserts )
        
        self._service_ids_to_applicable_service_ids = None
        self._service_ids_to_interested_service_ids = None
        
        return service_ids_to_sync
        
    
