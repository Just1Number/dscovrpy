PATH = '<path to dscovrpy output dir>'

local function get_timezone()
  local localdate = os.date("*t")
  local utcdate = os.date("!*t")
  localdate.isdst = false
  return os.difftime(os.time(localdate),  os.time(utcdate))
end

local function get_ts()
  local path = PATH .. 'image_info.epic'
  local file = io.open(path, "rb") -- r read mode and b binary mode
  if not file then return nil end
  local content = file:read "*a" -- *a or *all reads the whole file
  file:close()
  -- content = "epic_1b_20181006204346.png"
  local year = tonumber(string.sub(content, 9, 12))
  local month = tonumber(string.sub(content, 13, 14))
  local day = tonumber(string.sub(content, 15, 16))
  local hour = tonumber(string.sub(content, 17, 18))
  local minute = tonumber(string.sub(content, 19, 20))
  local second = tonumber(string.sub(content, 21, 22))
  ts = os.time{year=year, month=month, day=day, hour=hour, min=minute, sec=second}
  ts = ts + get_timezone()
  return ts
end

function conky_epic_date (f)
  if (f == nil) then
    return os.date("%c", get_ts())
  else
    return os.date(f, get_ts())
  end
end
