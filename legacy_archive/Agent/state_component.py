from abc import ABC, abstractmethod

class StateComponent(ABC):
    def __init__(self,value):
        self.value = value
        self.label = self._set_label(value)
        
    @abstractmethod
    def _set_label(self,value):
        pass

    def set_value(self,value):
        self.value = value
        self.label = self._set_label(value)

    def get_value(self):
        return self.value
    
    def get_label(self):
        return self.label
    
    @abstractmethod
    def get_index(self):
        pass

class NetworkState(StateComponent):
    """Network state value consist of 'private' or 'public'"""
    def _set_label(self, value):
        return value.lower()
    def get_index(self):
        mapping = {'private':0, 'public':1}
        return mapping[self.label]
    
class ThreatState(StateComponent):
    """Threat state value consist of integer number from 1-3"""
    def _set_label(self, value):
        if value > 2:
            return 'high'
        elif value > 1:
            return 'medium'
        else:
            return 'low'
    def get_index(self):
        mapping = {'low':0,'medium':1,'high':2}
        return mapping[self.label]
    
class BatteryState(StateComponent):
    """Battery state value consist of integer from 0-100"""
    def _set_label(self, value):
        digit = min(value//10,9)
        return f'{digit*10}-{(digit+1)*10}'
            
    def get_index(self):
        return min(self.value//10,9)
    
class SignalState(StateComponent):
    """Signal state value consist of integer value from 0-5"""
    def _set_label(self, value):
        if value == 5:
            return 'strong'
        elif value > 2:
            return 'medium'
        else:
            return 'weak'
    
    def get_index(self):
        mapping = {'weak':0,'medium':1,'strong':2}
        return mapping[self.label]
    
class SizeState(StateComponent):
    """Size state value consist of integer value larger than 0"""
    def _set_label(self, value):
        if value >= 250:
            return 'large'
        elif value >= 50:
            return 'medium'
        else:
            return 'small'
    def get_index(self):
        mapping = {'small':0,'medium':1,'large':2}
        return mapping[self.label]
    
class PriorityState(StateComponent):
    """Priority state value consist of integer value from 0-3"""
    def _set_label(self, value):
        if value > 2:
            return 'important'
        elif value > 1:
            return 'medium'
        else:
            return 'unimportant'
    def get_index(self):
        mapping = {'unimportant':0,'medium':1,'important':2}
        return mapping[self.label]