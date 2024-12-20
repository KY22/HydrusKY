# noinspection PyUnresolvedReferences
import numpy
# noinspection PyUnresolvedReferences
import numpy.core.multiarray # important this comes before cv!

# noinspection PyUnresolvedReferences
import cv2
from PIL import Image as PILImage
import warnings

try:
    
    # more hidden imports for pyinstaller
    
    # noinspection PyUnresolvedReferences
    import numpy.random.common  # pylint: disable=E0401
    # noinspection PyUnresolvedReferences
    import numpy.random.bounded_integers  # pylint: disable=E0401
    # noinspection PyUnresolvedReferences
    import numpy.random.entropy  # pylint: disable=E0401
    
except:
    
    pass # old version of numpy, screw it
    

if not hasattr( PILImage, 'DecompressionBombError' ):
    
    # super old versions don't have this, so let's just make a stub, wew
    
    class DBEStub( Warning ):
        
        pass
        
    
    PILImage.DecompressionBombError = DBEStub
    

if not hasattr( PILImage, 'DecompressionBombWarning' ):
    
    # super old versions don't have this, so let's just make a stub, wew
    
    class DBWStub( Warning ):
        
        pass
        
    
    PILImage.DecompressionBombWarning = DBWStub
    

warnings.simplefilter( 'ignore', PILImage.DecompressionBombWarning )
warnings.simplefilter( 'ignore', PILImage.DecompressionBombError )

# PIL moaning about weirdo TIFFs
warnings.filterwarnings( "ignore", "(Possibly )?corrupt EXIF data", UserWarning )
warnings.filterwarnings( "ignore", "Metadata Warning", UserWarning )

# PIL moaning about weirdo PNGs
warnings.filterwarnings( "ignore", "iTXt: chunk data is too large", UserWarning )
