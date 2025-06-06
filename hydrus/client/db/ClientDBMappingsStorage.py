import sqlite3

from hydrus.core import HydrusConstants as HC

from hydrus.client import ClientLocation
from hydrus.client.db import ClientDBMaintenance
from hydrus.client.db import ClientDBModule
from hydrus.client.db import ClientDBServices

def DoingAFileJoinTagSearchIsFaster( estimated_file_row_count, estimated_tag_row_count ):
    
    # ok, so there are times we want to do a tag search when we already know a superset of the file results (e.g. 'get all of these files that are tagged with samus')
    # sometimes it is fastest to just do the search using tag outer-join-loop/indices and intersect/difference in python
    # sometimes it is fastest to do the search with a temp file table and CROSS JOIN or EXISTS or similar to effect file outer-join-loop/indices
    
    # with experimental profiling, it is generally 2.5 times as slow to look up mappings using file indices. it also takes about 0.1 the time to set up temp table and other misc overhead
    # so, when we have file result A, and we want to fetch B, if the estimated size of A is < 2.6 the estimated size of B, we can save a bunch of time
    
    # normally, we could let sqlite do NATURAL JOIN analyze profiling, but that sometimes fails for me when the queries get complex, I believe due to my wewlad 'temp table' queries and weird tag/file index distribution
    
    file_lookup_speed_ratio = 2.5
    temp_table_overhead = 0.1
    
    return estimated_file_row_count * ( file_lookup_speed_ratio + temp_table_overhead ) < estimated_tag_row_count
    

MAPPINGS_CURRENT_PREFIX = 'current_mappings_'
MAPPINGS_DELETED_PREFIX = 'deleted_mappings_'
MAPPINGS_PENDING_PREFIX = 'pending_mappings_'
MAPPINGS_PETITIONED_PREFIX = 'petitioned_mappings_'

def GenerateMappingsTableNames( service_id: int ) -> tuple[ str, str, str, str ]:
    
    suffix = str( service_id )
    
    current_mappings_table_name = f'external_mappings.{MAPPINGS_CURRENT_PREFIX}{suffix}'
    
    deleted_mappings_table_name = f'external_mappings.{MAPPINGS_DELETED_PREFIX}{suffix}'
    
    pending_mappings_table_name = f'external_mappings.{MAPPINGS_PENDING_PREFIX}{suffix}'
    
    petitioned_mappings_table_name = f'external_mappings.{MAPPINGS_PETITIONED_PREFIX}{suffix}'
    
    return ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name )
    

SPECIFIC_DISPLAY_MAPPINGS_CURRENT_PREFIX = 'specific_display_current_mappings_cache_'
SPECIFIC_DISPLAY_MAPPINGS_PENDING_PREFIX = 'specific_display_pending_mappings_cache_'

def GenerateSpecificDisplayMappingsCacheTableNames( file_service_id, tag_service_id ):
    
    suffix = '{}_{}'.format( file_service_id, tag_service_id )
    
    cache_display_current_mappings_table_name = f'external_caches.{SPECIFIC_DISPLAY_MAPPINGS_CURRENT_PREFIX}{suffix}'
    
    cache_display_pending_mappings_table_name = f'external_caches.{SPECIFIC_DISPLAY_MAPPINGS_PENDING_PREFIX}{suffix}'
    
    return ( cache_display_current_mappings_table_name, cache_display_pending_mappings_table_name )
    

SPECIFIC_MAPPINGS_CURRENT_PREFIX = 'specific_current_mappings_cache_'
SPECIFIC_MAPPINGS_DELETED_PREFIX = 'specific_deleted_mappings_cache_'
SPECIFIC_MAPPINGS_PENDING_PREFIX = 'specific_pending_mappings_cache_'

def GenerateSpecificMappingsCacheTableNames( file_service_id, tag_service_id ):
    
    suffix = '{}_{}'.format( file_service_id, tag_service_id )
    
    cache_current_mappings_table_name = f'external_caches.{SPECIFIC_MAPPINGS_CURRENT_PREFIX}{suffix}'
    
    cache_deleted_mappings_table_name = f'external_caches.{SPECIFIC_MAPPINGS_DELETED_PREFIX}{suffix}'
    
    cache_pending_mappings_table_name = f'external_caches.{SPECIFIC_MAPPINGS_PENDING_PREFIX}{suffix}'
    
    return ( cache_current_mappings_table_name, cache_deleted_mappings_table_name, cache_pending_mappings_table_name )
    

class ClientDBMappingsStorage( ClientDBModule.ClientDBModule ):
    
    def __init__( self, cursor: sqlite3.Cursor, modules_db_maintenance: ClientDBMaintenance.ClientDBMaintenance, modules_services: ClientDBServices.ClientDBMasterServices ):
        
        self.modules_db_maintenance = modules_db_maintenance
        self.modules_services = modules_services
        
        super().__init__( 'client mappings storage', cursor )
        
    
    def _GetServiceIndexGenerationDict( self, service_id ) -> dict:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        index_generation_dict = {}
        
        index_generation_dict[ current_mappings_table_name ] = [
            ( [ 'hash_id', 'tag_id' ], True, 400 )
        ]
        
        index_generation_dict[ deleted_mappings_table_name ] = [
            ( [ 'hash_id', 'tag_id' ], True, 400 )
        ]
        
        index_generation_dict[ pending_mappings_table_name ] = [
            ( [ 'hash_id', 'tag_id' ], True, 400 )
        ]
        
        index_generation_dict[ petitioned_mappings_table_name ] = [
            ( [ 'hash_id', 'tag_id' ], True, 400 )
        ]
        
        return index_generation_dict
        
    
    def _GetServiceTableGenerationDict( self, service_id ) -> dict:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        return {
            current_mappings_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( tag_id INTEGER, hash_id INTEGER, PRIMARY KEY ( tag_id, hash_id ) ) WITHOUT ROWID;', 400 ),
            deleted_mappings_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( tag_id INTEGER, hash_id INTEGER, PRIMARY KEY ( tag_id, hash_id ) ) WITHOUT ROWID;', 400 ),
            pending_mappings_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( tag_id INTEGER, hash_id INTEGER, PRIMARY KEY ( tag_id, hash_id ) ) WITHOUT ROWID;', 400 ),
            petitioned_mappings_table_name : ( 'CREATE TABLE IF NOT EXISTS {} ( tag_id INTEGER, hash_id INTEGER, reason_id INTEGER, PRIMARY KEY ( tag_id, hash_id ) ) WITHOUT ROWID;', 400 )
        }
        
    
    def _GetServiceIdsWeGenerateDynamicTablesFor( self ):
        
        return self.modules_services.GetServiceIds( HC.REAL_TAG_SERVICES )
        
    
    def _GetServiceTablePrefixes( self ):
        
        return {
            MAPPINGS_CURRENT_PREFIX,
            MAPPINGS_DELETED_PREFIX,
            MAPPINGS_PENDING_PREFIX,
            MAPPINGS_PETITIONED_PREFIX
        }
        
    
    def ClearMappingsTables( self, service_id: int ):
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        self._Execute( 'DELETE FROM {};'.format( current_mappings_table_name ) )
        self._Execute( 'DELETE FROM {};'.format( deleted_mappings_table_name ) )
        self._Execute( 'DELETE FROM {};'.format( pending_mappings_table_name ) )
        self._Execute( 'DELETE FROM {};'.format( petitioned_mappings_table_name ) )
        
    
    def DropMappingsTables( self, service_id: int ):
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        self.modules_db_maintenance.DeferredDropTable( current_mappings_table_name )
        self.modules_db_maintenance.DeferredDropTable( deleted_mappings_table_name )
        self.modules_db_maintenance.DeferredDropTable( pending_mappings_table_name )
        self.modules_db_maintenance.DeferredDropTable( petitioned_mappings_table_name )
        
    
    def FilterExistingUpdateMappings( self, tag_service_id, mappings_ids, action ):
        
        if len( mappings_ids ) == 0:
            
            return mappings_ids
            
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( tag_service_id )
        
        culled_mappings_ids = []
        
        for row in mappings_ids:
            
            # mappings_ids here can have 'reason_id' for petitions, so we'll index our values here
            
            tag_id = row[0]
            hash_ids = row[1]
            
            if len( hash_ids ) == 0:
                
                continue
                
            elif len( hash_ids ) == 1:
                
                ( hash_id, ) = hash_ids
                
                if action == HC.CONTENT_UPDATE_ADD:
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( current_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        valid_hash_ids = hash_ids
                        
                    else:
                        
                        continue
                        
                    
                elif action == HC.CONTENT_UPDATE_DELETE:
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( deleted_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        valid_hash_ids = hash_ids
                        
                    else:
                        
                        continue
                        
                    
                elif action == HC.CONTENT_UPDATE_PEND:
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( petitioned_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is not None:
                        
                        # we can technically petition without a thing being current, so we do need to check for a conflict here!
                        
                        continue
                        
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( current_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( pending_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                        
                        if result is None:
                            
                            valid_hash_ids = hash_ids
                            
                        else:
                            
                            continue
                            
                        
                    else:
                        
                        continue
                        
                    
                elif action == HC.CONTENT_UPDATE_RESCIND_PEND:
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( pending_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        continue
                        
                    else:
                        
                        valid_hash_ids = hash_ids
                        
                    
                elif action == HC.CONTENT_UPDATE_PETITION:
                    
                    # we are technically ok with deleting things that are not current yet, so do not need to check for that!
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( pending_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is not None: # but not if they are pending lol
                        
                        continue
                        
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( petitioned_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        valid_hash_ids = hash_ids
                        
                    else:
                        
                        continue
                        
                    
                elif action == HC.CONTENT_UPDATE_RESCIND_PETITION:
                    
                    result = self._Execute( 'SELECT 1 FROM {} WHERE tag_id = ? AND hash_id = ?;'.format( petitioned_mappings_table_name ), ( tag_id, hash_id ) ).fetchone()
                    
                    if result is None:
                        
                        continue
                        
                    else:
                        
                        valid_hash_ids = hash_ids
                        
                    
                else:
                    
                    valid_hash_ids = set()
                    
                
            else:
                
                with self._MakeTemporaryIntegerTable( hash_ids, 'hash_id' ) as temp_hash_ids_table_name:
                    
                    if action == HC.CONTENT_UPDATE_ADD:
                        
                        existing_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, current_mappings_table_name ), ( tag_id, ) ) )
                        
                        valid_hash_ids = set( hash_ids ).difference( existing_hash_ids )
                        
                    elif action == HC.CONTENT_UPDATE_DELETE:
                        
                        existing_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, deleted_mappings_table_name ), ( tag_id, ) ) )
                        
                        valid_hash_ids = set( hash_ids ).difference( existing_hash_ids )
                        
                    elif action == HC.CONTENT_UPDATE_PEND:
                        
                        # prohibited hash_ids
                        existing_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, current_mappings_table_name ), ( tag_id, ) ) )
                        # existing_hash_ids
                        existing_hash_ids.update( self._STI( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, pending_mappings_table_name ), ( tag_id, ) ) ) )
                        # conflicting_hash_ids
                        existing_hash_ids.update( self._STI( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, petitioned_mappings_table_name ), ( tag_id, ) ) ) )
                        
                        valid_hash_ids = set( hash_ids ).difference( existing_hash_ids )
                        
                    elif action == HC.CONTENT_UPDATE_RESCIND_PEND:
                        
                        valid_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, pending_mappings_table_name ), ( tag_id, ) ) )
                        
                    elif action == HC.CONTENT_UPDATE_PETITION:
                        
                        # we are technically ok with deleting tags that don't exist yet!
                        existing_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, petitioned_mappings_table_name ), ( tag_id, ) ) )
                        # but we won't conflict with pending!
                        existing_hash_ids.update( self._STI( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, pending_mappings_table_name ), ( tag_id, ) ) ) )
                        
                        valid_hash_ids = set( hash_ids ).difference( existing_hash_ids )
                        
                    elif action == HC.CONTENT_UPDATE_RESCIND_PETITION:
                        
                        valid_hash_ids = self._STS( self._Execute( 'SELECT hash_id FROM {} CROSS JOIN {} USING ( hash_id ) WHERE tag_id = ?;'.format( temp_hash_ids_table_name, petitioned_mappings_table_name ), ( tag_id, ) ) )
                        
                    else:
                        
                        valid_hash_ids = set()
                        
                    
                
            
            if len( valid_hash_ids ) > 0:
                
                if action == HC.CONTENT_UPDATE_PETITION:
                    
                    reason_id = row[2]
                    
                    culled_mappings_ids.append( ( tag_id, valid_hash_ids, reason_id ) )
                    
                else:
                    
                    culled_mappings_ids.append( ( tag_id, valid_hash_ids ) )
                    
                
            
        
        return culled_mappings_ids
        
    
    def GenerateMappingsTables( self, service_id: int ):
        
        table_generation_dict = self._GetServiceTableGenerationDict( service_id )
        
        for ( table_name, ( create_query_without_name, version_added ) ) in table_generation_dict.items():
            
            self._CreateTable( create_query_without_name, table_name )
            
        
        index_generation_dict = self._GetServiceIndexGenerationDict( service_id )
        
        for ( table_name, columns, unique, version_added ) in self._FlattenIndexGenerationDict( index_generation_dict ):
            
            self._CreateIndex( table_name, columns, unique = unique )
            
        
    
    def GetCurrentFilesCount( self, service_id: int ) -> int:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        result = self._Execute( 'SELECT COUNT( DISTINCT hash_id ) FROM {};'.format( current_mappings_table_name ) ).fetchone()
        
        ( count, ) = result
        
        return count
        
    
    def GetDeletedMappingsCount( self, service_id: int ) -> int:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        result = self._Execute( 'SELECT COUNT( * ) FROM {};'.format( deleted_mappings_table_name ) ).fetchone()
        
        ( count, ) = result
        
        return count
        
    
    def GetFastestStorageMappingTableNames( self, file_service_id: int, tag_service_id: int ):
        
        statuses_to_table_names = {}
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( tag_service_id )
        
        statuses_to_table_names[ HC.CONTENT_STATUS_CURRENT ] = current_mappings_table_name
        statuses_to_table_names[ HC.CONTENT_STATUS_DELETED ] = deleted_mappings_table_name
        statuses_to_table_names[ HC.CONTENT_STATUS_PENDING ] = pending_mappings_table_name
        statuses_to_table_names[ HC.CONTENT_STATUS_PETITIONED ] = petitioned_mappings_table_name
        
        if file_service_id != self.modules_services.combined_file_service_id:
            
            ( cache_current_mappings_table_name, cache_deleted_mappings_table_name, cache_pending_mappings_table_name ) = GenerateSpecificMappingsCacheTableNames( file_service_id, tag_service_id )
            
            statuses_to_table_names[ HC.CONTENT_STATUS_CURRENT ] = cache_current_mappings_table_name
            statuses_to_table_names[ HC.CONTENT_STATUS_DELETED ] = cache_deleted_mappings_table_name
            statuses_to_table_names[ HC.CONTENT_STATUS_PENDING ] = cache_pending_mappings_table_name
            
        
        return statuses_to_table_names
        
    
    def GetFastestStorageMappingTableNamesFromLocationContext( self, location_context: ClientLocation.LocationContext, tag_service_id: int ):
        
        # TODO: this can probably work better, e.g. if we have multiple local domains we can return all local files or whatever
        
        if location_context.IncludesDeleted() and not location_context.IncludesCurrent():
            
            known_fast_covering_file_service_id = self.modules_services.combined_deleted_file_service_id
            
        elif location_context.IsOneDomain():
            
            file_service_key = list( location_context.current_service_keys )[0]
            
            known_fast_covering_file_service_id = self.modules_services.GetServiceId( file_service_key )
            
        else:
            
            known_fast_covering_file_service_id = self.modules_services.combined_file_service_id 
            
        
        return self.GetFastestStorageMappingTableNames( known_fast_covering_file_service_id, tag_service_id )
        
    
    def GetPendingMappingsCount( self, service_id: int ) -> int:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        result = self._Execute( 'SELECT COUNT( * ) FROM {};'.format( pending_mappings_table_name ) ).fetchone()
        
        ( count, ) = result
        
        return count
        
    
    def GetPetitionedMappingsCount( self, service_id: int ) -> int:
        
        ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
        
        result = self._Execute( 'SELECT COUNT( * ) FROM {};'.format( petitioned_mappings_table_name ) ).fetchone()
        
        ( count, ) = result
        
        return count
        
    
    def GetTablesAndColumnsThatUseDefinitions( self, content_type: int ) -> list[ tuple[ str, str ] ]:
        
        tables_and_columns = []
        
        if content_type == HC.CONTENT_TYPE_HASH:
            
            for service_id in self.modules_services.GetServiceIds( HC.REAL_TAG_SERVICES ):
                
                ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
                
                tables_and_columns.extend( [
                    ( current_mappings_table_name, 'hash_id' ),
                    ( deleted_mappings_table_name, 'hash_id' ),
                    ( pending_mappings_table_name, 'hash_id' ),
                    ( petitioned_mappings_table_name, 'hash_id' )
                ] )
                
            
        elif content_type == HC.CONTENT_TYPE_TAG:
            
            for service_id in self.modules_services.GetServiceIds( HC.REAL_TAG_SERVICES ):
                
                ( current_mappings_table_name, deleted_mappings_table_name, pending_mappings_table_name, petitioned_mappings_table_name ) = GenerateMappingsTableNames( service_id )
                
                tables_and_columns.extend( [
                    ( current_mappings_table_name, 'tag_id' ),
                    ( deleted_mappings_table_name, 'tag_id' ),
                    ( pending_mappings_table_name, 'tag_id' ),
                    ( petitioned_mappings_table_name, 'tag_id' )
                ] )
                
            
        
        return tables_and_columns
        
    
