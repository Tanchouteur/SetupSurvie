package.path = '/opt/?.lua;' .. package.path
local base = dofile('/opt/car.lua')
local process = base.process_way
base.process_way = function(profile, way, result, relations)
  if way:get_value_by_key('route') == 'ferry' then return end
  if way:get_value_by_key('highway') == 'track' and way:get_value_by_key('tracktype') ~= 'grade1' then return end
  return process(profile, way, result, relations)
end
return base
