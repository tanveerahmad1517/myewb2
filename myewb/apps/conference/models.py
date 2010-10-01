import hashlib
from datetime import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _

from conference.constants import *
from networks.models import Network, ChapterInfo

class ConferenceRegistration(models.Model):
    """Conference registration data"""
    
    user = models.ForeignKey(User, related_name="conference_registrations")
    chapter = models.ForeignKey(Network, related_name="conference_delegates", null=True)
    
    amountPaid = models.DecimalField(max_digits=6, decimal_places=2)
    roomSize = models.IntegerField()
    type = models.CharField(max_length=50)
    date = models.DateTimeField(default=datetime.now)
    headset = models.BooleanField(default=False)
    foodPrefs = models.CharField(max_length=10, choices=FOOD_CHOICES, default='none')
    cancelled = models.BooleanField(default=False)
    specialNeeds = models.TextField()
    emergName = models.CharField(max_length=255)
    emergPhone = models.CharField(max_length=50)
    code = models.ForeignKey('ConferenceCode', related_name="registration")
    prevConfs = models.SmallIntegerField()
    prevRetreats = models.SmallIntegerField()
    
    challenge = models.TextField()
    malawiwatsan = models.SmallIntegerField()
    malawiagric =  models.SmallIntegerField()
    ghanaagric = models.SmallIntegerField()
    burkinaagric = models.SmallIntegerField()
    ghanagari = models.SmallIntegerField()
    
    txid = models.CharField(max_length=255)
    receiptNum = models.CharField(max_length=255)
    africaFund = models.BooleanField()

    def cancel(self):
        self.cancelled = True
        self.chapter = None
        
    def getRefundAmount(self):
        return self.amountPaid - 20

class InvalidCode(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)
    
class ConferenceCode(models.Model):
    """Registration code"""

    code = models.CharField(max_length=9)
    type = models.CharField(max_length=1, choices=CONF_CODES)
    number = models.IntegerField()
    
    generated = models.DateTimeField(default=datetime.now)
    
    # currently needs to be done manually, but fairly easy to write a UI for this
    expired = models.BooleanField(default=False)
    
    # not currently used, but may let us enforce code/chapter pairings
    chapter = models.ForeignKey(Network, related_name="conference_codes", verbose_name=_('chapter'), null=True)
    
    def __init__(self, *args, **kwargs):
        super(ConferenceCode, self).__init__(*args, **kwargs)
    
        # try/except to keep the admin page working
        try:
            self.type = kwargs['type']
            self.number = kwargs['number']
        
            self.expired = False

            m = hashlib.md5()
            m.update("%s%03d%s" % (self.type, self.number, CONF_HASH))
            self.code = "%s%03d%s" % (self.type, self.number, m.hexdigest()[:4])
        except:
            pass

    def getShortname(self):
        # CONF_CODES is a tuple so that it can be used as a choices= for 
        # the type field above... so we hack it here to make it act like a
        # dictionary
        for code in CONF_CODES:
            if code[0] == self.type:
                return code[1]
        
        # should never get here, since the type field is restricted to CONF_CODES
        return "unknown"
    
    def isAvailable(self):
        if self.expired == True:
            return False
        
        try:
            ConferenceCode.objects.get(code=self.code, registration__cancelled=False)
        except ObjectDoesNotExist:
            return True
        except:
            pass

        return False

    @staticmethod
    def isValid(code):
        type = code[0]
        number = code[1:3]
        codehash = code[4:]
        
        m = hashlib.md5()
        m.update("%s%s%s" % (type, number, CONF_HASH))
        return codehash == m.hexdigest()[:4]