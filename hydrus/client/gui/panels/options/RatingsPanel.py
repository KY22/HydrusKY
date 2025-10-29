from qtpy import QtWidgets as QW

from hydrus.core import HydrusConstants as HC

from hydrus.client import ClientConstants as CC
from hydrus.client.gui import ClientGUIFunctions
from hydrus.client.gui import QtPorting as QP
from hydrus.client.gui.panels.options import ClientGUIOptionsPanelBase
from hydrus.client.gui.widgets import ClientGUICommon

class RatingsPanel( ClientGUIOptionsPanelBase.OptionsPagePanel ):
    
    def __init__( self, parent, new_options ):
        
        super().__init__( parent )
        
        self._new_options = new_options
        
        #
        
        media_viewer_rating_panel = ClientGUICommon.StaticBox( self, 'media viewer' )
        
        self._media_viewer_rating_icon_size_px = ClientGUICommon.BetterDoubleSpinBox( media_viewer_rating_panel, min = 1.0, max = 255.0 )
        self._media_viewer_rating_icon_size_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set size in pixels for like, numerical, and inc/dec rating icons for clicking on. This will be used for both width and height of the square icons.' ) )
        self._media_viewer_rating_incdec_height_px = ClientGUICommon.BetterDoubleSpinBox( media_viewer_rating_panel, min = 2.0, max = 255.0 )
        self._media_viewer_rating_incdec_height_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set height in pixels for inc/dec rectangles in the media viewer. Width will be dynamic based on the rating. It is limited to be between twice and half of the normal ratings icons sizes.' ) )
        
        
        thumbnail_ratings_panel = ClientGUICommon.StaticBox( self, 'thumbnails' )
        
        ( thumbnail_width, thumbnail_height ) = HC.options[ 'thumbnail_dimensions' ]
        
        self._draw_thumbnail_rating_background = QW.QCheckBox( thumbnail_ratings_panel )
        tt = 'If you show any ratings on your thumbnails (you can set this under _services->manage services_), they can get lost in the noise of the underlying thumb. This draws a plain flat rectangle around them in the normal window panel colour. If you think it is ugly, turn it off here!'
        self._draw_thumbnail_rating_background.setToolTip( ClientGUIFunctions.WrapToolTip( tt ) )
        
        self._draw_thumbnail_rating_icon_size_px = ClientGUICommon.BetterDoubleSpinBox( thumbnail_ratings_panel, min = 1.0, max = thumbnail_width )
        tt = 'This is the size of any rating icons shown in pixels. It will be square, so this is both the width and height.'
        self._draw_thumbnail_rating_icon_size_px.setToolTip( ClientGUIFunctions.WrapToolTip( tt ) )
        
        self._draw_thumbnail_rating_incdec_height_px = ClientGUICommon.BetterDoubleSpinBox( thumbnail_ratings_panel, min = 2.0, max = thumbnail_width )
        tt = 'This is the width of the inc/dec rating buttons in pixels. Height is 1/2 this. Limited to a range around the rating icon sizes.'
        self._draw_thumbnail_rating_incdec_height_px.setToolTip( ClientGUIFunctions.WrapToolTip( tt ) )
        
        self._draw_thumbnail_numerical_ratings_collapsed_always = QW.QCheckBox( thumbnail_ratings_panel )
        tt = 'If this is checked, all numerical ratings will show collapsed in thumbnails (\'2/10 ▲\' instead of \'▲▲▼▼▼▼▼▼▼▼\') regardless of the per-service setting.'
        self._draw_thumbnail_numerical_ratings_collapsed_always.setToolTip( ClientGUIFunctions.WrapToolTip( tt ) )
        
        
        preview_window_rating_panel = ClientGUICommon.StaticBox( self, 'preview window' )
        
        self._preview_window_rating_icon_size_px = ClientGUICommon.BetterDoubleSpinBox( preview_window_rating_panel, min = 1.0, max = 255.0 )
        self._preview_window_rating_icon_size_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set size in pixels for like and numerical rating icons for clicking on in the preview window.' ) )
        
        self._preview_window_rating_incdec_height_px  = ClientGUICommon.BetterDoubleSpinBox( preview_window_rating_panel, min = 2.0, max = 255.0 )
        self._preview_window_rating_incdec_height_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set height in pixels for inc/dec rectangles in the preview window. Width will be dynamic based on the rating. It is limited to be between twice and half of the normal ratings icons sizes.' ) )
        
        
        manage_ratings_popup_panel = ClientGUICommon.StaticBox( self, 'dialogs' )
        
        self._dialog_rating_icon_size_px = ClientGUICommon.BetterDoubleSpinBox( manage_ratings_popup_panel, min = 6.0, max = 128.0 )
        self._dialog_rating_icon_size_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set size in pixels for like and numerical rating icons for clicking on in the \'manage ratings\' dialog.' ) )
        
        self._dialog_rating_incdec_height_px = ClientGUICommon.BetterDoubleSpinBox( manage_ratings_popup_panel, min = 12.0, max = 128.0 )
        self._dialog_rating_incdec_height_px.setToolTip( ClientGUIFunctions.WrapToolTip( 'Set height in pixels for inc/dec rectangles in the \'manage ratings\' dialog.  Width will be dynamic based on the rating. It is limited to be between twice and half of the normal ratings icons sizes.' ) )
        
        #clamp inc/dec rectangles to min 0.5 and max 2x rating stars px for rating size stuff
        self._media_viewer_rating_icon_size_px.editingFinished.connect( self._icon_size_changed )
        self._draw_thumbnail_rating_icon_size_px.editingFinished.connect( self._icon_size_changed )
        self._preview_window_rating_icon_size_px.editingFinished.connect( self._icon_size_changed )
        
        #
        
        self._media_viewer_rating_icon_size_px.setValue( self._new_options.GetFloat( 'media_viewer_rating_icon_size_px' ) )
        self._media_viewer_rating_incdec_height_px.setValue( self._new_options.GetFloat( 'media_viewer_rating_incdec_height_px' ) )
        
        self._draw_thumbnail_rating_background.setChecked( self._new_options.GetBoolean( 'draw_thumbnail_rating_background' ) )
        self._draw_thumbnail_numerical_ratings_collapsed_always.setChecked( self._new_options.GetBoolean( 'draw_thumbnail_numerical_ratings_collapsed_always' ) )
        self._draw_thumbnail_rating_icon_size_px.setValue( self._new_options.GetFloat( 'draw_thumbnail_rating_icon_size_px' ) )
        self._draw_thumbnail_rating_incdec_height_px.setValue( self._new_options.GetFloat( 'thumbnail_rating_incdec_height_px' )  )
        
        self._preview_window_rating_icon_size_px.setValue( self._new_options.GetFloat( 'preview_window_rating_icon_size_px' ) )
        self._preview_window_rating_incdec_height_px.setValue( self._new_options.GetFloat( 'preview_window_rating_incdec_height_px' ) )
        
        self._dialog_rating_icon_size_px.setValue( self._new_options.GetFloat( 'dialog_rating_icon_size_px' ) )
        self._dialog_rating_incdec_height_px.setValue( self._new_options.GetFloat( 'dialog_rating_incdec_height_px' ) )
        
        #
        
        rows = []
        
        rows.append( ( 'Media viewer like/dislike and numerical rating icon size:', self._media_viewer_rating_icon_size_px ) )
        rows.append( ( 'Media viewer inc/dec rating icon height:', self._media_viewer_rating_incdec_height_px ) )
        
        media_viewer_rating_gridbox = ClientGUICommon.WrapInGrid( media_viewer_rating_panel, rows )
        media_viewer_rating_panel.Add( media_viewer_rating_gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        rows = []
        
        rows.append( ( 'Preview window like/dislike and numerical rating icon size:', self._preview_window_rating_icon_size_px ) )
        rows.append( ( 'Preview window inc/dec rating icon height:', self._preview_window_rating_incdec_height_px ) )
        
        preview_hovers_gridbox = ClientGUICommon.WrapInGrid( preview_window_rating_panel, rows )
        preview_window_rating_panel.Add( preview_hovers_gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        rows = []
        
        rows.append( ( 'Thumbnail like/dislike and numerical rating icon size: ', self._draw_thumbnail_rating_icon_size_px ) )
        rows.append( ( 'Thumbnail inc/dec rating height: ', self._draw_thumbnail_rating_incdec_height_px ) )
        rows.append( ( 'Give thumbnail ratings a flat background: ', self._draw_thumbnail_rating_background ) )
        rows.append( ( 'Always draw thumbnail numerical ratings collapsed: ', self._draw_thumbnail_numerical_ratings_collapsed_always ) )
        
        thumbnail_ratings_gridbox = ClientGUICommon.WrapInGrid( thumbnail_ratings_panel, rows )
        thumbnail_ratings_panel.Add( thumbnail_ratings_gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        rows = []
        
        rows.append( ( 'Dialogs like/dislike and numerical rating icon size:', self._dialog_rating_icon_size_px ) )
        rows.append( ( 'Dialogs inc/dec rating height:', self._dialog_rating_incdec_height_px ) )
        
        manage_ratings_gridbox = ClientGUICommon.WrapInGrid( manage_ratings_popup_panel, rows )
        
        manage_ratings_popup_panel.Add( manage_ratings_gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        media_viewer_rating_gridbox.setColumnStretch(0, 1)
        media_viewer_rating_gridbox.setColumnStretch(1, 1)
        preview_hovers_gridbox.setColumnStretch(0, 1)
        preview_hovers_gridbox.setColumnStretch(1, 1)
        thumbnail_ratings_gridbox.setColumnStretch(0, 1)
        thumbnail_ratings_gridbox.setColumnStretch(1, 1)
        manage_ratings_gridbox.setColumnStretch(0, 1)
        manage_ratings_gridbox.setColumnStretch(1, 1)
        
        vbox = QP.VBoxLayout()
        
        QP.AddToLayout( vbox, media_viewer_rating_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        QP.AddToLayout( vbox, preview_window_rating_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        QP.AddToLayout( vbox, thumbnail_ratings_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        QP.AddToLayout( vbox, manage_ratings_popup_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        vbox.addStretch( 0 )
        self.setLayout( vbox )
        
    
    def _icon_size_changed( self ):
        
        new_value = self._media_viewer_rating_icon_size_px.value()
        
        self._media_viewer_rating_incdec_height_px.setMaximum( new_value * 2 )
        self._media_viewer_rating_incdec_height_px.setMinimum( new_value * 0.5 )
        
        new_value = self._preview_window_rating_icon_size_px.value()
        
        self._preview_window_rating_incdec_height_px.setMaximum( new_value * 2 )
        self._preview_window_rating_incdec_height_px.setMinimum( new_value * 0.5 )
        
        new_value = self._draw_thumbnail_rating_icon_size_px.value()
        
        self._draw_thumbnail_rating_incdec_height_px.setMaximum( new_value * 2 )
        self._draw_thumbnail_rating_incdec_height_px.setMinimum( new_value * 0.5 )
        
    
    def UpdateOptions( self ):
        
        self._new_options.SetFloat( 'media_viewer_rating_icon_size_px', self._media_viewer_rating_icon_size_px.value() )
        self._new_options.SetFloat( 'media_viewer_rating_incdec_height_px', self._media_viewer_rating_incdec_height_px.value() )
        
        self._new_options.SetBoolean( 'draw_thumbnail_rating_background', self._draw_thumbnail_rating_background.isChecked() )
        self._new_options.SetBoolean( 'draw_thumbnail_numerical_ratings_collapsed_always', self._draw_thumbnail_numerical_ratings_collapsed_always.isChecked() )
        self._new_options.SetFloat( 'draw_thumbnail_rating_icon_size_px', self._draw_thumbnail_rating_icon_size_px.value() )
        self._new_options.SetFloat( 'thumbnail_rating_incdec_height_px', self._draw_thumbnail_rating_incdec_height_px.value() )
        
        self._new_options.SetFloat( 'preview_window_rating_icon_size_px', self._preview_window_rating_icon_size_px.value() )
        self._new_options.SetFloat( 'preview_window_rating_incdec_height_px', self._preview_window_rating_incdec_height_px.value() )
        
        self._new_options.SetFloat( 'dialog_rating_icon_size_px', self._dialog_rating_icon_size_px.value() )
        self._new_options.SetFloat( 'dialog_rating_incdec_height_px', self._dialog_rating_incdec_height_px.value() )
        
    
