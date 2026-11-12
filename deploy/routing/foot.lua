-- Conservative household planning: no ferries or aerialways.
package.path = '/opt/?.lua;' .. package.path
local base = dofile('/opt/foot.lua')
local process = base.process_way
base.process_way = function(profile, way, result, relations)
  if way:get_value_by_key('route') == 'ferry' or way:get_value_by_key('aerialway') ~= '' then return end
  local difficulty = way:get_value_by_key('sac_scale')
  if difficulty ~= '' and difficulty ~= 'hiking' then return end
  return process(profile, way, result, relations)
end
return base
