from qtpy import QtWidgets as QW

from hydrus.client import ClientConstants as CC
from hydrus.client.gui import ClientGUIFunctions
from hydrus.client.gui import QtPorting as QP
from hydrus.client.gui.panels import ClientGUIScrolledPanels
from hydrus.client.gui.widgets import ClientGUICommon

class QuestionYesNoPanel( ClientGUIScrolledPanels.ResizingScrolledPanel ):
    
    def __init__( self, parent, message, yes_label = 'yes', no_label = 'no' ):
        
        ClientGUIScrolledPanels.ResizingScrolledPanel.__init__( self, parent )
        
        self._yes = ClientGUICommon.BetterButton( self, yes_label, self.parentWidget().done, QW.QDialog.Accepted )
        self._yes.setObjectName( 'HydrusAccept' )
        
        self._no = ClientGUICommon.BetterButton( self, no_label, self.parentWidget().done, QW.QDialog.Rejected )
        self._no.setObjectName( 'HydrusCancel' )
        
        #
        
        hbox = QP.HBoxLayout()
        
        QP.AddToLayout( hbox, self._yes, CC.FLAGS_CENTER_PERPENDICULAR )
        QP.AddToLayout( hbox, self._no, CC.FLAGS_CENTER_PERPENDICULAR )
        
        vbox = QP.VBoxLayout()
        
        text = ClientGUICommon.BetterStaticText( self, message )
        text.setWordWrap( True )
        
        QP.AddToLayout( vbox, text, CC.FLAGS_EXPAND_BOTH_WAYS )
        QP.AddToLayout( vbox, hbox, CC.FLAGS_ON_RIGHT )
        
        self.widget().setLayout( vbox )
        
        ClientGUIFunctions.SetFocusLater( self._yes )
        
    

class QuestionYesYesNoPanel( ClientGUIScrolledPanels.ResizingScrolledPanel ):
    
    def __init__( self, parent, message, yes_tuples = None, no_label = 'no' ):
        
        ClientGUIScrolledPanels.ResizingScrolledPanel.__init__( self, parent )
        
        if yes_tuples is None:
            
            yes_tuples = [ ( 'yes', 'yes' ) ]
            
        
        self._value = yes_tuples[0][1]
        
        yes_buttons = []
        
        for ( label, data ) in yes_tuples:
            
            yes_button = ClientGUICommon.BetterButton( self, label, self._DoYes, data )
            yes_button.setObjectName( 'HydrusAccept' )
            
            yes_buttons.append( yes_button )
            
        
        self._no = ClientGUICommon.BetterButton( self, no_label, self.parentWidget().done, QW.QDialog.Rejected )
        self._no.setObjectName( 'HydrusCancel' )
        
        #
        
        text = ClientGUICommon.BetterStaticText( self, message )
        text.setWordWrap( True )
        
        hbox = QP.HBoxLayout()
        
        for yes_button in yes_buttons:
            
            QP.AddToLayout( hbox, yes_button, CC.FLAGS_CENTER_PERPENDICULAR )
            
        
        QP.AddToLayout( hbox, self._no, CC.FLAGS_CENTER_PERPENDICULAR )
        
        vbox = QP.VBoxLayout()
        
        QP.AddToLayout( vbox, text, CC.FLAGS_EXPAND_BOTH_WAYS )
        QP.AddToLayout( vbox, hbox, CC.FLAGS_ON_RIGHT )
        
        self.widget().setLayout( vbox )
        
        ClientGUIFunctions.SetFocusLater( yes_buttons[0] )
        
    
    def _DoYes( self, value ):
        
        self._value = value
        
        self.parentWidget().done( QW.QDialog.Accepted )
        
    
    def GetValue( self ):
        
        return self._value
        
    
