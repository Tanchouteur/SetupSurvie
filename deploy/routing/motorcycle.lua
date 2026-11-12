package.path = '/opt/?.lua;' .. package.path
local base = dofile('/opt/car.lua')
local setup_car = base.setup
base.setup = function()
  local profile = setup_car()
  profile.access_tags_hierarchy = Sequence {'motorcycle', 'motor_vehicle', 'vehicle', 'access'}
  profile.restrictions = Sequence {'motorcycle', 'motor_vehicle', 'vehicle'}
  profile.vehicle_width = 1.0
  profile.vehicle_height = 2.0
  profile.vehicle_length = 2.5
  profile.vehicle_weight = 350
  return profile
end
local process = base.process_way
base.process_way = function(profile, way, result, relations)
  if way:get_value_by_key('route') == 'ferry' then return end
  if way:get_value_by_key('highway') == 'track' and way:get_value_by_key('tracktype') ~= 'grade1' then return end
  return process(profile, way, result, relations)
end
return base
