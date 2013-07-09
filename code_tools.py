import math
import smtplib
from email.mime.text import MIMEText
import numpy as np
from  getpass import getuser
import datetime
import numpy as np
from os import path,makedirs
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.io as sio

class ConfigureDataSet(object):
    def __init__(self):
        self.Username = getuser() 
        self.Date = datetime.datetime.now()   
        self.DirectoryRoot = '/media/Data'
        self.ExperimentDir = ''
        self.FileNamePrefix = ''
        self.mode = ''
        self.SingleFrequency = 0
        self.FreqStart = 0
        self.FreqStop = 0
        self.Freq_num_pts = 0
        self.TestSet = 'S21' #transmission always for this experiment
        self.X_length = 0
        self.Y_length = 0
        self.X_res = 0
        self.Y_res = 0
        self.X_origin = 0
        self.Y_origin = 0
        '''Where the origin of the crystal is located '''   
        self.Num_x_pts = 0
        self.Num_y_pts = 0
        self.x_port = ''
        self.y_port = ''
        
    def make_sub_dirs(self):
        p = path.join(self.DirectoryRoot,self.ExperimentDir)
        if not path.exists(p):
            makedirs(p)
        
        self.mag_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Single_Point','Mag')
        if not path.exists(self.mag_point_dir):
            makedirs(self.mag_point_dir)

        self.phase_point_dir = path.join(self.DirectoryRoot,self.ExperimentDir,'Single_Point','Phase')
        if not path.exists(self.phase_point_dir):
            makedirs(self.phase_point_dir)  
        

    def set_xy_num_pts(self):
        self.Num_x_pts = int(np.ceil(self.X_length / self.X_res))
        self.Num_y_pts = int(np.ceil(self.Y_length / self.Y_res))

class CodeTools(object):
    '''Contains methods used for the combination of motor tools and vna tools '''    
    
    def _notify_admin_error(self, username, date, traceback):

        email_body = """
%(username)s
%(date)s

%(traceback)s
""" %{'username':username,'date':date,'traceback':traceback}

        # Create a text/plain message
        msg = MIMEText(email_body)

        # me == the sender's email address
        me = 'Man Lab Data Machine'
        # you == the recipient's email address
        recipients = ['wmanlab@gmail.com', 'dpcuneo@gmail.com','theebbandflow@yahoo.com']
        msg['Subject'] = 'Automatically generated email.'
        msg['From'] = "Dr. Man's Lab Linux Machine."
        msg['To'] = 'System Admin.'

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.starttls()
        s.login('wmanlab','debye100!')
        s.sendmail(me, recipients, msg.as_string())
        s.quit()

    def ToSI(self,d):
        if d == 0.0 or d == 0:
            return 0

        incPrefixes = ['k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        decPrefixes = ['mm', 'mu', 'n', 'p', 'f', 'a', 'z', 'y']

        degree = int(math.floor(math.log10(math.fabs(d)) / 3))
        
        prefix = ''

        if degree!=0:
            ds = degree/math.fabs(degree)
            if ds == 1:
                if degree - 1 < len(incPrefixes):
                    prefix = incPrefixes[degree - 1]
                else:
                    prefix = incPrefixes[-1]
                    degree = len(incPrefixes)
            elif ds == -1:
                if -degree - 1 < len(decPrefixes):
                    prefix = decPrefixes[-degree - 1]
                else:
                    prefix = decPrefixes[-1]
                    degree = -len(decPrefixes)

            scaled = float(d * math.pow(1000, -degree))
            s = "{scaled} {prefix}".format(scaled=scaled, prefix=prefix)

        else:
            s = "{d}".format(d=d)

        return(s)

class ArrayTools(object):
    def __init__(self, Config):
        self.config = Config
  
    def save_readme(self):
        header_template = '''
Directory = %(path)s
FreqStart = %(freq_start)s
FreqStop =  %(freq_stop)s
Freq_num_pts = %(freq_res)s
X_length = %(x_len)s
X_res = %(x_res)s
Y_length = %(y_len)s
Y_res = %(y_res)s
Username = %(user)s
Date = %(date)s
Origin = %(origin)s
 ''' %{'path':path.join(self.config.DirectoryRoot,self.config.ExperimentDir),
       'freq_start':self.config.FreqStart,
       'freq_stop':self.config.FreqStop,
       'freq_res':self.config.Freq_num_pts,
       'x_len':self.config.X_length,
       'y_len':self.config.Y_length,
       'x_res':self.config.X_res,
       'y_res':self.config.Y_res,
       'user':self.config.Username,
       'date':self.config.Date,
       'origin':self.config.Origin}

        fullpath = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,self.config.FileNamePrefix + '_README.dat')
        f = open(fullpath,'w')
        f.write(header_template)
        f.close()

    def save_data_to_file(self, data_point, data, type):  
        '''This method saves each data point vector into a text file. The arg 'type'
        is 'mag' or 'phase' . The data type arg is used to chronologically number the points for
        a later reconstruction. The files are saved into their respective sub dirs, Mag and Phase.''' 
        
        file_name = "%(name_prefix)s_%(type)s_%(file_num)s.dat" %{'name_prefix':self.config.FileNamePrefix
                                                        ,'file_num':str(data_point).zfill(5),
                                                        'type':type
                                                        }
        if type == 'mag':
            fullpath = path.join(self.config.mag_point_dir, file_name)    
        elif type == 'phase':
            fullpath = path.join(self.config.phase_point_dir, file_name) 
        else:
            raise Exception, "You did not supply an accepted type of 'mag' or 'phase'. "
        
        np.savetxt(fullpath, data)
          
        print "File Saved Successfully.\n"

    def make_3d_array(self):
        '''Initialize a numpy 3D or 2D array for storing Mag or Phase data. This is for using PYthon to
        view the data during the experiment. The lab protocol for storing the data for outside analysis is to
        save all the real and imaginary parts as separate long column of text values. '''
        
        array = np.zeros((self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))
        
        return array
    
    def get_magnitude(self, data):
        '''Takes col of complex numbers and returns col of mag. '''
        mag_data = np.zeros(data.shape, dtype=float)
        mag_data = np.abs(data)
        
        return mag_data 

    def get_phase(self,data):
        '''Takes cols of complex and returns col of phase '''
        phase_data = np.zeros(data.shape,dtype=float)
        phase_data = np.angle(data, False)# no degrees only radians

        return phase_data
   
    def make_freq_vector(self):
        Deltafreq = (self.config.freqstop - self.config.freqstart) / float(self.config.Freq_num_pts)
        freq_vec = np.arange(self.config.FreqStart, self.config.FreqStop, Deltafreq)

    def load_data_files(self, type):
        '''loads all data point files into a 1D array of either mag or phase data. 
        Use reshape_1D_to_3D() to get back a numpy 3D array. Returns the 1D data array.'''

        num_pts = self.config.Num_x_pts * self.config.Num_y_pts
        data = np.zeros((self.config.Freq_num_pts,num_pts))

        for i in xrange(0,self.config.Num_x_pts - 1):
            for j in xrange(0,self.config.Num_x_pts - 1):
                file_num = i * self.config.Num_x_pts + j
                file_name = "%(name_prefix)s_%(type)s_%(file_num)s.dat" %{'name_prefix':self.config.FileNamePrefix,
                                                        'file_num':str(data_point).zfill(5),
                                                        'type':type
                                                         }
                
                path_str = path.join(self.config.DirectoryRoot, self.config.ExperimentDir, file_name)
                data[:,file_num] = np.loadtxt(path_str,dtype='float',comments='#',delimiter='\n')
                print "file: %i loaded into array\n" %file_num 
        
        return data    

    def reshape_1D_to_3D(self, data):        
        '''Takes col of data and writes a 3D array to disk. Used if the automatic 3D array is NOT being used. 
        FOr instance, you retook some data points and want to compile a new 3D matrix (ascii format)'''      
        outdata = np.zeros((self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))  
        outdata = np.reshape(data,(self.config.Freq_num_pts,self.config.Num_y_pts,self.config.Num_x_pts))
        
        return outdata
     
    def save_flattened_array(self,data):
        '''The only way to save n dim array as text, is to flatten it out into 1D array, load into 
        program like matlab, then reshape. '''
        dim1 = str(self.config.Num_y_pts)
        dim2 = str(self.config.Num_x_pts)
        dim3 = str(self.config.Freq_num_pts)
        fname = "%s_flattened_%s_%s_%s.txt " %(self.config.FileNamePrefix,dim1,dim2,dim3)      
        fullpath = path.join(self.config.DirectoryRoot,self.config.ExperimentDir,fname)
        np.savetxt(fullpath, data)    
                                  
class PlotTools(object):
    def __init__(self, Config):
        self.config = Config 
        plt.figure()
        plt.ion()    
        dummy = np.zeros((self.config.Num_x_pts,self.config.Num_y_pts))
        im = plt.imshow(dummy, interpolation='nearest', origin='lower', cmap = plt.cm.jet)       
        plt.colorbar(im)   
               
    def plot(self, mag, phase, z=0):
        '''Plot the data in-vivo as a check on the experiment using numpy. The z arg is the
        xy plane you want to plot. For single point mode, z = 0 (default), for sweep you must choose. '''
        plt.subplot(1,2,1)
        im = plt.imshow(mag[z,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   
        plt.subplot(1,2,2)
        im = plt.imshow(phase[z,:,:], interpolation='nearest', origin='lower', cmap = plt.cm.jet)   

        plt.draw()
        
    def close_plot(self):
        plt.close('all')
        
















