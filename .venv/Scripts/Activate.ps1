<#
.Synopsis
Activate a Python virtual environment for the current PowerShell session.

.Description
Pushes the python executable for a virtual environment to the front of the
$Env:PATH environment variable and sets the prompt to signify that you are
in a Python virtual environment. Makes use of the command line switches as
well as the `pyvenv.cfg` file values present in the virtual environment.

.Parameter VenvDir
Path to the directory that contains the virtual environment to activate. The
default value for this is the parent of the directory that the Activate.ps1
script is located within.

.Parameter Prompt
The prompt prefix to display when this virtual environment is activated. By
default, this prompt is the name of the virtual environment folder (VenvDir)
surrounded by parentheses and followed by a single space (ie. '(.venv) ').

.Example
Activate.ps1
Activates the Python virtual environment that contains the Activate.ps1 script.

.Example
Activate.ps1 -Verbose
Activates the Python virtual environment that contains the Activate.ps1 script,
and shows extra information about the activation as it executes.

.Example
Activate.ps1 -VenvDir C:\Users\MyUser\Common\.venv
Activates the Python virtual environment located in the specified location.

.Example
Activate.ps1 -Prompt "MyPython"
Activates the Python virtual environment that contains the Activate.ps1 script,
and prefixes the current prompt with the specified string (surrounded in
parentheses) while the virtual environment is active.

.Notes
On Windows, it may be required to enable this Activate.ps1 script by setting the
execution policy for the user. You can do this by issuing the following PowerShell
command:

PS C:\> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

For more information on Execution Policies: 
https://go.microsoft.com/fwlink/?LinkID=135170

#>
Param(
    [Parameter(Mandatory = $false)]
    [String]
    $VenvDir,
    [Parameter(Mandatory = $false)]
    [String]
    $Prompt
)

<# Function declarations --------------------------------------------------- #>

<#
.Synopsis
Remove all shell session elements added by the Activate script, including the
addition of the virtual environment's Python executable from the beginning of
the PATH variable.

.Parameter NonDestructive
If present, do not remove this function from the global namespace for the
session.

#>
function global:deactivate ([switch]$NonDestructive) {
    # Revert to original values

    # The prior prompt:
    if (Test-Path -Path Function:_OLD_VIRTUAL_PROMPT) {
        Copy-Item -Path Function:_OLD_VIRTUAL_PROMPT -Destination Function:prompt
        Remove-Item -Path Function:_OLD_VIRTUAL_PROMPT
    }

    # The prior PYTHONHOME:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PYTHONHOME) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME -Destination Env:PYTHONHOME
        Remove-Item -Path Env:_OLD_VIRTUAL_PYTHONHOME
    }

    # The prior PATH:
    if (Test-Path -Path Env:_OLD_VIRTUAL_PATH) {
        Copy-Item -Path Env:_OLD_VIRTUAL_PATH -Destination Env:PATH
        Remove-Item -Path Env:_OLD_VIRTUAL_PATH
    }

    # Just remove the VIRTUAL_ENV altogether:
    if (Test-Path -Path Env:VIRTUAL_ENV) {
        Remove-Item -Path env:VIRTUAL_ENV
    }

    # Just remove VIRTUAL_ENV_PROMPT altogether.
    if (Test-Path -Path Env:VIRTUAL_ENV_PROMPT) {
        Remove-Item -Path env:VIRTUAL_ENV_PROMPT
    }

    # Just remove the _PYTHON_VENV_PROMPT_PREFIX altogether:
    if (Get-Variable -Name "_PYTHON_VENV_PROMPT_PREFIX" -ErrorAction SilentlyContinue) {
        Remove-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Scope Global -Force
    }

    # Leave deactivate function in the global namespace if requested:
    if (-not $NonDestructive) {
        Remove-Item -Path function:deactivate
    }
}

<#
.Description
Get-PyVenvConfig parses the values from the pyvenv.cfg file located in the
given folder, and returns them in a map.

For each line in the pyvenv.cfg file, if that line can be parsed into exactly
two strings separated by `=` (with any amount of whitespace surrounding the =)
then it is considered a `key = value` line. The left hand string is the key,
the right hand is the value.

If the value starts with a `'` or a `"` then the first and last character is
stripped from the value before being captured.

.Parameter ConfigDir
Path to the directory that contains the `pyvenv.cfg` file.
#>
function Get-PyVenvConfig(
    [String]
    $ConfigDir
) {
    Write-Verbose "Given ConfigDir=$ConfigDir, obtain values in pyvenv.cfg"

    # Ensure the file exists, and issue a warning if it doesn't (but still allow the function to continue).
    $pyvenvConfigPath = Join-Path -Resolve -Path $ConfigDir -ChildPath 'pyvenv.cfg' -ErrorAction Continue

    # An empty map will be returned if no config file is found.
    $pyvenvConfig = @{ }

    if ($pyvenvConfigPath) {

        Write-Verbose "File exists, parse `key = value` lines"
        $pyvenvConfigContent = Get-Content -Path $pyvenvConfigPath

        $pyvenvConfigContent | ForEach-Object {
            $keyval = $PSItem -split "\s*=\s*", 2
            if ($keyval[0] -and $keyval[1]) {
                $val = $keyval[1]

                # Remove extraneous quotations around a string value.
                if ("'""".Contains($val.Substring(0, 1))) {
                    $val = $val.Substring(1, $val.Length - 2)
                }

                $pyvenvConfig[$keyval[0]] = $val
                Write-Verbose "Adding Key: '$($keyval[0])'='$val'"
            }
        }
    }
    return $pyvenvConfig
}


<# Begin Activate script --------------------------------------------------- #>

# Determine the containing directory of this script
$VenvExecPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvExecDir = Get-Item -Path $VenvExecPath

Write-Verbose "Activation script is located in path: '$VenvExecPath'"
Write-Verbose "VenvExecDir Fullname: '$($VenvExecDir.FullName)"
Write-Verbose "VenvExecDir Name: '$($VenvExecDir.Name)"

# Set values required in priority: CmdLine, ConfigFile, Default
# First, get the location of the virtual environment, it might not be
# VenvExecDir if specified on the command line.
if ($VenvDir) {
    Write-Verbose "VenvDir given as parameter, using '$VenvDir' to determine values"
}
else {
    Write-Verbose "VenvDir not given as a parameter, using parent directory name as VenvDir."
    $VenvDir = $VenvExecDir.Parent.FullName.TrimEnd("\\/")
    Write-Verbose "VenvDir=$VenvDir"
}

# Next, read the `pyvenv.cfg` file to determine any required value such
# as `prompt`.
$pyvenvCfg = Get-PyVenvConfig -ConfigDir $VenvDir

# Next, set the prompt from the command line, or the config file, or
# just use the name of the virtual environment folder.
if ($Prompt) {
    Write-Verbose "Prompt specified as argument, using '$Prompt'"
}
else {
    Write-Verbose "Prompt not specified as argument to script, checking pyvenv.cfg value"
    if ($pyvenvCfg -and $pyvenvCfg['prompt']) {
        Write-Verbose "  Setting based on value in pyvenv.cfg='$($pyvenvCfg['prompt'])'"
        $Prompt = $pyvenvCfg['prompt'];
    }
    else {
        Write-Verbose "  Setting prompt based on parent's directory's name. (Is the directory name passed to venv module when creating the virtual environment)"
        Write-Verbose "  Got leaf-name of $VenvDir='$(Split-Path -Path $venvDir -Leaf)'"
        $Prompt = Split-Path -Path $venvDir -Leaf
    }
}

Write-Verbose "Prompt = '$Prompt'"
Write-Verbose "VenvDir='$VenvDir'"

# Deactivate any currently active virtual environment, but leave the
# deactivate function in place.
deactivate -nondestructive

# Now set the environment variable VIRTUAL_ENV, used by many tools to determine
# that there is an activated venv.
$env:VIRTUAL_ENV = $VenvDir

$env:VIRTUAL_ENV_PROMPT = $Prompt

if (-not $Env:VIRTUAL_ENV_DISABLE_PROMPT) {

    Write-Verbose "Setting prompt to '$Prompt'"

    # Set the prompt to include the env name
    # Make sure _OLD_VIRTUAL_PROMPT is global
    function global:_OLD_VIRTUAL_PROMPT { "" }
    Copy-Item -Path function:prompt -Destination function:_OLD_VIRTUAL_PROMPT
    New-Variable -Name _PYTHON_VENV_PROMPT_PREFIX -Description "Python virtual environment prompt prefix" -Scope Global -Option ReadOnly -Visibility Public -Value $Prompt

    function global:prompt {
        Write-Host -NoNewline -ForegroundColor Green "($_PYTHON_VENV_PROMPT_PREFIX) "
        _OLD_VIRTUAL_PROMPT
    }
}

# Clear PYTHONHOME
if (Test-Path -Path Env:PYTHONHOME) {
    Copy-Item -Path Env:PYTHONHOME -Destination Env:_OLD_VIRTUAL_PYTHONHOME
    Remove-Item -Path Env:PYTHONHOME
}

# Add the venv to the PATH
Copy-Item -Path Env:PATH -Destination Env:_OLD_VIRTUAL_PATH
$Env:PATH = "$VenvExecDir$([System.IO.Path]::PathSeparator)$Env:PATH"

# SIG # Begin signature block
# MII0HQYJKoZIhvcNAQcCoII0DjCCNAoCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCBALKwKRFIhr2RY
# IW/WJLd9pc8a9sj/IoThKU92fTfKsKCCG9IwggXMMIIDtKADAgECAhBUmNLR1FsZ
# lUgTecgRwIeZMA0GCSqGSIb3DQEBDAUAMHcxCzAJBgNVBAYTAlVTMR4wHAYDVQQK
# ExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xSDBGBgNVBAMTP01pY3Jvc29mdCBJZGVu
# dGl0eSBWZXJpZmljYXRpb24gUm9vdCBDZXJ0aWZpY2F0ZSBBdXRob3JpdHkgMjAy
# MDAeFw0yMDA0MTYxODM2MTZaFw00NTA0MTYxODQ0NDBaMHcxCzAJBgNVBAYTAlVT
# MR4wHAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xSDBGBgNVBAMTP01pY3Jv
# c29mdCBJZGVudGl0eSBWZXJpZmljYXRpb24gUm9vdCBDZXJ0aWZpY2F0ZSBBdXRo
# b3JpdHkgMjAyMDCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBALORKgeD
# Bmf9np3gx8C3pOZCBH8Ppttf+9Va10Wg+3cL8IDzpm1aTXlT2KCGhFdFIMeiVPvH
# or+Kx24186IVxC9O40qFlkkN/76Z2BT2vCcH7kKbK/ULkgbk/WkTZaiRcvKYhOuD
# PQ7k13ESSCHLDe32R0m3m/nJxxe2hE//uKya13NnSYXjhr03QNAlhtTetcJtYmrV
# qXi8LW9J+eVsFBT9FMfTZRY33stuvF4pjf1imxUs1gXmuYkyM6Nix9fWUmcIxC70
# ViueC4fM7Ke0pqrrBc0ZV6U6CwQnHJFnni1iLS8evtrAIMsEGcoz+4m+mOJyoHI1
# vnnhnINv5G0Xb5DzPQCGdTiO0OBJmrvb0/gwytVXiGhNctO/bX9x2P29Da6SZEi3
# W295JrXNm5UhhNHvDzI9e1eM80UHTHzgXhgONXaLbZ7LNnSrBfjgc10yVpRnlyUK
# xjU9lJfnwUSLgP3B+PR0GeUw9gb7IVc+BhyLaxWGJ0l7gpPKWeh1R+g/OPTHU3mg
# trTiXFHvvV84wRPmeAyVWi7FQFkozA8kwOy6CXcjmTimthzax7ogttc32H83rwjj
# O3HbbnMbfZlysOSGM1l0tRYAe1BtxoYT2v3EOYI9JACaYNq6lMAFUSw0rFCZE4e7
# swWAsk0wAly4JoNdtGNz764jlU9gKL431VulAgMBAAGjVDBSMA4GA1UdDwEB/wQE
# AwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBTIftJqhSobyhmYBAcnz1AQ
# T2ioojAQBgkrBgEEAYI3FQEEAwIBADANBgkqhkiG9w0BAQwFAAOCAgEAr2rd5hnn
# LZRDGU7L6VCVZKUDkQKL4jaAOxWiUsIWGbZqWl10QzD0m/9gdAmxIR6QFm3FJI9c
# Zohj9E/MffISTEAQiwGf2qnIrvKVG8+dBetJPnSgaFvlVixlHIJ+U9pW2UYXeZJF
# xBA2CFIpF8svpvJ+1Gkkih6PsHMNzBxKq7Kq7aeRYwFkIqgyuH4yKLNncy2RtNwx
# AQv3Rwqm8ddK7VZgxCwIo3tAsLx0J1KH1r6I3TeKiW5niB31yV2g/rarOoDXGpc8
# FzYiQR6sTdWD5jw4vU8w6VSp07YEwzJ2YbuwGMUrGLPAgNW3lbBeUU0i/OxYqujY
# lLSlLu2S3ucYfCFX3VVj979tzR/SpncocMfiWzpbCNJbTsgAlrPhgzavhgplXHT2
# 6ux6anSg8Evu75SjrFDyh+3XOjCDyft9V77l4/hByuVkrrOj7FjshZrM77nq81YY
# uVxzmq/FdxeDWds3GhhyVKVB0rYjdaNDmuV3fJZ5t0GNv+zcgKCf0Xd1WF81E+Al
# GmcLfc4l+gcK5GEh2NQc5QfGNpn0ltDGFf5Ozdeui53bFv0ExpK91IjmqaOqu/dk
# ODtfzAzQNb50GQOmxapMomE2gj4d8yu8l13bS3g7LfU772Aj6PXsCyM2la+YZr9T
# 03u4aUoqlmZpxJTG9F9urJh4iIAGXKKy7aIwggb+MIIE5qADAgECAhMzAAM/y2Wy
# WWnFfpZcAAAAAz/LMA0GCSqGSIb3DQEBDAUAMFoxCzAJBgNVBAYTAlVTMR4wHAYD
# VQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xKzApBgNVBAMTIk1pY3Jvc29mdCBJ
# RCBWZXJpZmllZCBDUyBBT0MgQ0EgMDEwHhcNMjUwNDA4MDEwNzI0WhcNMjUwNDEx
# MDEwNzI0WjB8MQswCQYDVQQGEwJVUzEPMA0GA1UECBMGT3JlZ29uMRIwEAYDVQQH
# EwlCZWF2ZXJ0b24xIzAhBgNVBAoTGlB5dGhvbiBTb2Z0d2FyZSBGb3VuZGF0aW9u
# MSMwIQYDVQQDExpQeXRob24gU29mdHdhcmUgRm91bmRhdGlvbjCCAaIwDQYJKoZI
# hvcNAQEBBQADggGPADCCAYoCggGBAI0elXEcbTdGLOszMU2fzimHGM9Y4EjwFgC2
# iGPdieHc0dK1DyEIdtnvjKxnG/KICC3J2MrhePGzMEkie3yQjx05B5leG0q8YoGU
# m9z9K67V6k3DSXX0vQe9FbaNVuyXed31MEf/qek7Zo4ELxu8n/LO3ibURBLRHNoW
# Dz9zr4DcU+hha0bdIL6SnKMLwHqRj59gtFFEPqXcOVO7kobkzQS3O1T5KNL/zGuW
# UGQln7fS4YI9bj24bfrSeG/QzLgChVYScxnUgjAANfT1+SnSxrT4/esMtfbcvfID
# BIvOWk+FPPj9IQWsAMEG/LLG4cF/pQ/TozUXKx362GJBbe6paTM/RCUTcffd83h2
# bXo9vXO/roZYk6H0ecd2h2FFzLUQn/0i4RQQSOp6zt1eDf28h6F8ev+YYKcChph8
# iRt32bJPcLQVbUzhehzT4C0pz6oAqPz8s0BGvlj1G6r4CY1Cs2YiMU09/Fl64pWf
# IsA/ReaYj6yNsgQZNUcvzobK2mTxMwIDAQABo4ICGTCCAhUwDAYDVR0TAQH/BAIw
# ADAOBgNVHQ8BAf8EBAMCB4AwPAYDVR0lBDUwMwYKKwYBBAGCN2EBAAYIKwYBBQUH
# AwMGGysGAQQBgjdhgqKNuwqmkohkgZH0oEWCk/3hbzAdBgNVHQ4EFgQU4Y4Xr/Xn
# zEXblXrNC0ZLdaPEJYUwHwYDVR0jBBgwFoAU6IPEM9fcnwycdpoKptTfh6ZeWO4w
# ZwYDVR0fBGAwXjBcoFqgWIZWaHR0cDovL3d3dy5taWNyb3NvZnQuY29tL3BraW9w
# cy9jcmwvTWljcm9zb2Z0JTIwSUQlMjBWZXJpZmllZCUyMENTJTIwQU9DJTIwQ0El
# MjAwMS5jcmwwgaUGCCsGAQUFBwEBBIGYMIGVMGQGCCsGAQUFBzAChlhodHRwOi8v
# d3d3Lm1pY3Jvc29mdC5jb20vcGtpb3BzL2NlcnRzL01pY3Jvc29mdCUyMElEJTIw
# VmVyaWZpZWQlMjBDUyUyMEFPQyUyMENBJTIwMDEuY3J0MC0GCCsGAQUFBzABhiFo
# dHRwOi8vb25lb2NzcC5taWNyb3NvZnQuY29tL29jc3AwZgYDVR0gBF8wXTBRBgwr
# BgEEAYI3TIN9AQEwQTA/BggrBgEFBQcCARYzaHR0cDovL3d3dy5taWNyb3NvZnQu
# Y29tL3BraW9wcy9Eb2NzL1JlcG9zaXRvcnkuaHRtMAgGBmeBDAEEATANBgkqhkiG
# 9w0BAQwFAAOCAgEAKTeVGPXsDKqQLe1OuKx6K6q711FPxNQyLOOqeenH8zybHwNo
# k05cMk39HQ7u+R9BQIL0bWexb7wa3XeKaX06p7aY/OQs+ycvUi/fC6RGlaLWmQ9D
# YhZn2TBz5znimvSf3P+aidCuXeDU5c8GpBFog6fjEa/k+n7TILi0spuYZ4yC9R48
# R63/VvpLi2SqxfJbx5n92bY6driNzAntjoravF25BSejXVrdzefbnqbQnZPB39g8
# XHygGPb0912fIuNKPLQa/uCnmYdXJnPb0ZgMxxA8fyxvL2Q30Qf5xpFDssPDElvD
# DoAbvR24CWvuHbu+CMMr2SJUpX4RRvDioO7JeB6wZb+64MXyPUSSf6QwkKNsHPIa
# e9tSfREh86sYn5bOA0Wd+Igk0RpA5jDRTu3GgPOPWbm1PU+VoeqThtHt6R3l17pr
# aQ5wIuuLXgxi1K4ZWgtvXw8BtIXfZz24qCtoo0+3kEGUpEHBgkF1SClbRb8uAzx+
# 0ROGniLPJRU20Xfn7CgipeKLcNn33JPFwQHk1zpbGS0090mi0erOQCz0S47YdHmm
# RJcbkNIL9DeNAglTZ/TFxrYUM1NRS1Cp4e63MgBKcWh9VJNokInzzmS+bofZz+u1
# mm8YNtiJjdT8fmizXdUEk68EXQhOs0+HBNvc9nMRK6R28MZu/J+PaUcPL84wggda
# MIIFQqADAgECAhMzAAAABzeMW6HZW4zUAAAAAAAHMA0GCSqGSIb3DQEBDAUAMGMx
# CzAJBgNVBAYTAlVTMR4wHAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xNDAy
# BgNVBAMTK01pY3Jvc29mdCBJRCBWZXJpZmllZCBDb2RlIFNpZ25pbmcgUENBIDIw
# MjEwHhcNMjEwNDEzMTczMTU0WhcNMjYwNDEzMTczMTU0WjBaMQswCQYDVQQGEwJV
# UzEeMBwGA1UEChMVTWljcm9zb2Z0IENvcnBvcmF0aW9uMSswKQYDVQQDEyJNaWNy
# b3NvZnQgSUQgVmVyaWZpZWQgQ1MgQU9DIENBIDAxMIICIjANBgkqhkiG9w0BAQEF
# AAOCAg8AMIICCgKCAgEAt/fAAygHxbo+jxA04hNI8bz+EqbWvSu9dRgAawjCZau1
# Y54IQal5ArpJWi8cIj0WA+mpwix8iTRguq9JELZvTMo2Z1U6AtE1Tn3mvq3mywZ9
# SexVd+rPOTr+uda6GVgwLA80LhRf82AvrSwxmZpCH/laT08dn7+Gt0cXYVNKJORm
# 1hSrAjjDQiZ1Jiq/SqiDoHN6PGmT5hXKs22E79MeFWYB4y0UlNqW0Z2LPNua8k0r
# bERdiNS+nTP/xsESZUnrbmyXZaHvcyEKYK85WBz3Sr6Et8Vlbdid/pjBpcHI+Hyt
# oaUAGE6rSWqmh7/aEZeDDUkz9uMKOGasIgYnenUk5E0b2U//bQqDv3qdhj9UJYWA
# DNYC/3i3ixcW1VELaU+wTqXTxLAFelCi/lRHSjaWipDeE/TbBb0zTCiLnc9nmOjZ
# PKlutMNho91wxo4itcJoIk2bPot9t+AV+UwNaDRIbcEaQaBycl9pcYwWmf0bJ4IF
# n/CmYMVG1ekCBxByyRNkFkHmuMXLX6PMXcveE46jMr9syC3M8JHRddR4zVjd/FxB
# nS5HOro3pg6StuEPshrp7I/Kk1cTG8yOWl8aqf6OJeAVyG4lyJ9V+ZxClYmaU5yv
# tKYKk1FLBnEBfDWw+UAzQV0vcLp6AVx2Fc8n0vpoyudr3SwZmckJuz7R+S79BzMC
# AwEAAaOCAg4wggIKMA4GA1UdDwEB/wQEAwIBhjAQBgkrBgEEAYI3FQEEAwIBADAd
# BgNVHQ4EFgQU6IPEM9fcnwycdpoKptTfh6ZeWO4wVAYDVR0gBE0wSzBJBgRVHSAA
# MEEwPwYIKwYBBQUHAgEWM2h0dHA6Ly93d3cubWljcm9zb2Z0LmNvbS9wa2lvcHMv
# RG9jcy9SZXBvc2l0b3J5Lmh0bTAZBgkrBgEEAYI3FAIEDB4KAFMAdQBiAEMAQTAS
# BgNVHRMBAf8ECDAGAQH/AgEAMB8GA1UdIwQYMBaAFNlBKbAPD2Ns72nX9c0pnqRI
# ajDmMHAGA1UdHwRpMGcwZaBjoGGGX2h0dHA6Ly93d3cubWljcm9zb2Z0LmNvbS9w
# a2lvcHMvY3JsL01pY3Jvc29mdCUyMElEJTIwVmVyaWZpZWQlMjBDb2RlJTIwU2ln
# bmluZyUyMFBDQSUyMDIwMjEuY3JsMIGuBggrBgEFBQcBAQSBoTCBnjBtBggrBgEF
# BQcwAoZhaHR0cDovL3d3dy5taWNyb3NvZnQuY29tL3BraW9wcy9jZXJ0cy9NaWNy
# b3NvZnQlMjBJRCUyMFZlcmlmaWVkJTIwQ29kZSUyMFNpZ25pbmclMjBQQ0ElMjAy
# MDIxLmNydDAtBggrBgEFBQcwAYYhaHR0cDovL29uZW9jc3AubWljcm9zb2Z0LmNv
# bS9vY3NwMA0GCSqGSIb3DQEBDAUAA4ICAQB3/utLItkwLTp4Nfh99vrbpSsL8NwP
# Ij2+TBnZGL3C8etTGYs+HZUxNG+rNeZa+Rzu9oEcAZJDiGjEWytzMavD6Bih3nEW
# FsIW4aGh4gB4n/pRPeeVrK4i1LG7jJ3kPLRhNOHZiLUQtmrF4V6IxtUFjvBnijaZ
# 9oIxsSSQP8iHMjP92pjQrHBFWHGDbkmx+yO6Ian3QN3YmbdfewzSvnQmKbkiTibJ
# gcJ1L0TZ7BwmsDvm+0XRsPOfFgnzhLVqZdEyWww10bflOeBKqkb3SaCNQTz8nsha
# UZhrxVU5qNgYjaaDQQm+P2SEpBF7RolEC3lllfuL4AOGCtoNdPOWrx9vBZTXAVdT
# E2r0IDk8+5y1kLGTLKzmNFn6kVCc5BddM7xoDWQ4aUoCRXcsBeRhsclk7kVXP+zJ
# GPOXwjUJbnz2Kt9iF/8B6FDO4blGuGrogMpyXkuwCC2Z4XcfyMjPDhqZYAPGGTUI
# NMtFbau5RtGG1DOWE9edCahtuPMDgByfPixvhy3sn7zUHgIC/YsOTMxVuMQi/bga
# memo/VNKZrsZaS0nzmOxKpg9qDefj5fJ9gIHXcp2F0OHcVwe3KnEXa8kqzMDfrRl
# /wwKrNSFn3p7g0b44Ad1ONDmWt61MLQvF54LG62i6ffhTCeoFT9Z9pbUo2gxlyTF
# g7Bm0fgOlnRfGDCCB54wggWGoAMCAQICEzMAAAAHh6M0o3uljhwAAAAAAAcwDQYJ
# KoZIhvcNAQEMBQAwdzELMAkGA1UEBhMCVVMxHjAcBgNVBAoTFU1pY3Jvc29mdCBD
# b3Jwb3JhdGlvbjFIMEYGA1UEAxM/TWljcm9zb2Z0IElkZW50aXR5IFZlcmlmaWNh
# dGlvbiBSb290IENlcnRpZmljYXRlIEF1dGhvcml0eSAyMDIwMB4XDTIxMDQwMTIw
# MDUyMFoXDTM2MDQwMTIwMTUyMFowYzELMAkGA1UEBhMCVVMxHjAcBgNVBAoTFU1p
# Y3Jvc29mdCBDb3Jwb3JhdGlvbjE0MDIGA1UEAxMrTWljcm9zb2Z0IElEIFZlcmlm
# aWVkIENvZGUgU2lnbmluZyBQQ0EgMjAyMTCCAiIwDQYJKoZIhvcNAQEBBQADggIP
# ADCCAgoCggIBALLwwK8ZiCji3VR6TElsaQhVCbRS/3pK+MHrJSj3Zxd3KU3rlfL3
# qrZilYKJNqztA9OQacr1AwoNcHbKBLbsQAhBnIB34zxf52bDpIO3NJlfIaTE/xrw
# eLoQ71lzCHkD7A4As1Bs076Iu+mA6cQzsYYH/Cbl1icwQ6C65rU4V9NQhNUwgrx9
# rGQ//h890Q8JdjLLw0nV+ayQ2Fbkd242o9kH82RZsH3HEyqjAB5a8+Ae2nPIPc8s
# ZU6ZE7iRrRZywRmrKDp5+TcmJX9MRff241UaOBs4NmHOyke8oU1TYrkxh+YeHgfW
# o5tTgkoSMoayqoDpHOLJs+qG8Tvh8SnifW2Jj3+ii11TS8/FGngEaNAWrbyfNrC6
# 9oKpRQXY9bGH6jn9NEJv9weFxhTwyvx9OJLXmRGbAUXN1U9nf4lXezky6Uh/cgjk
# Vd6CGUAf0K+Jw+GE/5VpIVbcNr9rNE50Sbmy/4RTCEGvOq3GhjITbCa4crCzTTHg
# YYjHs1NbOc6brH+eKpWLtr+bGecy9CrwQyx7S/BfYJ+ozst7+yZtG2wR461uckFu
# 0t+gCwLdN0A6cFtSRtR8bvxVFyWwTtgMMFRuBa3vmUOTnfKLsLefRaQcVTgRnzeL
# zdpt32cdYKp+dhr2ogc+qM6K4CBI5/j4VFyC4QFeUP2YAidLtvpXRRo3AgMBAAGj
# ggI1MIICMTAOBgNVHQ8BAf8EBAMCAYYwEAYJKwYBBAGCNxUBBAMCAQAwHQYDVR0O
# BBYEFNlBKbAPD2Ns72nX9c0pnqRIajDmMFQGA1UdIARNMEswSQYEVR0gADBBMD8G
# CCsGAQUFBwIBFjNodHRwOi8vd3d3Lm1pY3Jvc29mdC5jb20vcGtpb3BzL0RvY3Mv
# UmVwb3NpdG9yeS5odG0wGQYJKwYBBAGCNxQCBAweCgBTAHUAYgBDAEEwDwYDVR0T
# AQH/BAUwAwEB/zAfBgNVHSMEGDAWgBTIftJqhSobyhmYBAcnz1AQT2ioojCBhAYD
# VR0fBH0wezB5oHegdYZzaHR0cDovL3d3dy5taWNyb3NvZnQuY29tL3BraW9wcy9j
# cmwvTWljcm9zb2Z0JTIwSWRlbnRpdHklMjBWZXJpZmljYXRpb24lMjBSb290JTIw
# Q2VydGlmaWNhdGUlMjBBdXRob3JpdHklMjAyMDIwLmNybDCBwwYIKwYBBQUHAQEE
# gbYwgbMwgYEGCCsGAQUFBzAChnVodHRwOi8vd3d3Lm1pY3Jvc29mdC5jb20vcGtp
# b3BzL2NlcnRzL01pY3Jvc29mdCUyMElkZW50aXR5JTIwVmVyaWZpY2F0aW9uJTIw
# Um9vdCUyMENlcnRpZmljYXRlJTIwQXV0aG9yaXR5JTIwMjAyMC5jcnQwLQYIKwYB
# BQUHMAGGIWh0dHA6Ly9vbmVvY3NwLm1pY3Jvc29mdC5jb20vb2NzcDANBgkqhkiG
# 9w0BAQwFAAOCAgEAfyUqnv7Uq+rdZgrbVyNMul5skONbhls5fccPlmIbzi+OwVdP
# Q4H55v7VOInnmezQEeW4LqK0wja+fBznANbXLB0KrdMCbHQpbLvG6UA/Xv2pfpVI
# E1CRFfNF4XKO8XYEa3oW8oVH+KZHgIQRIwAbyFKQ9iyj4aOWeAzwk+f9E5StNp5T
# 8FG7/VEURIVWArbAzPt9ThVN3w1fAZkF7+YU9kbq1bCR2YD+MtunSQ1Rft6XG7b4
# e0ejRA7mB2IoX5hNh3UEauY0byxNRG+fT2MCEhQl9g2i2fs6VOG19CNep7SquKaB
# jhWmirYyANb0RJSLWjinMLXNOAga10n8i9jqeprzSMU5ODmrMCJE12xS/NWShg/t
# uLjAsKP6SzYZ+1Ry358ZTFcx0FS/mx2vSoU8s8HRvy+rnXqyUJ9HBqS0DErVLjQw
# K8VtsBdekBmdTbQVoCgPCqr+PDPB3xajYnzevs7eidBsM71PINK2BoE2UfMwxCCX
# 3mccFgx6UsQeRSdVVVNSyALQe6PT12418xon2iDGE81OGCreLzDcMAZnrUAx4XQL
# Uz6ZTl65yPUiOh3k7Yww94lDf+8oG2oZmDh5O1Qe38E+M3vhKwmzIeoB1dVLlz4i
# 3IpaDcR+iuGjH2TdaC1ZOmBXiCRKJLj4DT2uhJ04ji+tHD6n58vhavFIrmcxgheh
# MIIXnQIBATBxMFoxCzAJBgNVBAYTAlVTMR4wHAYDVQQKExVNaWNyb3NvZnQgQ29y
# cG9yYXRpb24xKzApBgNVBAMTIk1pY3Jvc29mdCBJRCBWZXJpZmllZCBDUyBBT0Mg
# Q0EgMDECEzMAAz/LZbJZacV+llwAAAADP8swDQYJYIZIAWUDBAIBBQCggcwwGQYJ
# KoZIhvcNAQkDMQwGCisGAQQBgjcCAQQwHAYKKwYBBAGCNwIBCzEOMAwGCisGAQQB
# gjcCARUwLwYJKoZIhvcNAQkEMSIEICpXe3RS3b2coD0CJveEHlglqtPUYZ2FqSrO
# UfP6C6Y4MGAGCisGAQQBgjcCAQwxUjBQoEqASABCAHUAaQBsAHQAOgAgAFIAZQBs
# AGUAYQBzAGUAXwB2ADMALgAxADQALgAwAGEANwBfADIAMAAyADUAMAA0ADAAOAAu
# ADAAMaECgAAwDQYJKoZIhvcNAQEBBQAEggGASZeEVq0b6gGFC+dClCAGzpyJDpiy
# DNl/tzFDBolAw3y5OGKw/9zsCYix2tK7Rg77ZcY5sPxXFwv+GhhSuTqn/uwz09+a
# aHRSkZKAlXGmTHjEMUbigJlz8gA3fBtk4LTohAzmm40rDLQWFpDjHS8tNA90zuDa
# K44+nsjCdBZYzEYNbEq/XudjPEc2ySH8x4S59XEr0/xHPEtNcMCRn+f5y56AF+XQ
# j2Yx5POniAx6KKSeVoh0npSrmNZNH+wakncNZH04TJs7VNafNqFzVFk+DNFnjBeG
# sY3GrYfDVI0jq+XoTmR/olV07HHClj3t1tl51f7zKWqma0j09MTN5eSNUsF6LaII
# bJCnxMXDMe4sDF+OqILN7PrQFcgkbQ1wirvXGAhYDfH+omS4xMT70KI0AzZHwkGl
# S1fBt9PESTfpbJm7pg5Un6/85id6c0uqlcRGLpCMJLevaWLdEOSY88cGr5okjqp2
# BBC4rQNFwRSwo3Ei5HC7lGyh04mEaDMRVnVIoYIUsjCCFK4GCisGAQQBgjcDAwEx
# ghSeMIIUmgYJKoZIhvcNAQcCoIIUizCCFIcCAQMxDzANBglghkgBZQMEAgEFADCC
# AWoGCyqGSIb3DQEJEAEEoIIBWQSCAVUwggFRAgEBBgorBgEEAYRZCgMBMDEwDQYJ
# YIZIAWUDBAIBBQAEIFPFSzQNUlTV5/+16T0ZheqlmLrkjp1W8msVyHm9MoB9AgZn
# 5T+2MfoYEzIwMjUwNDA4MTMxNzU5LjQ5OFowBIACAfSggemkgeYwgeMxCzAJBgNV
# BAYTAlVTMRMwEQYDVQQIEwpXYXNoaW5ndG9uMRAwDgYDVQQHEwdSZWRtb25kMR4w
# HAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xLTArBgNVBAsTJE1pY3Jvc29m
# dCBJcmVsYW5kIE9wZXJhdGlvbnMgTGltaXRlZDEnMCUGA1UECxMeblNoaWVsZCBU
# U1MgRVNOOjdBMUEtMDVFMC1EOTQ3MTUwMwYDVQQDEyxNaWNyb3NvZnQgUHVibGlj
# IFJTQSBUaW1lIFN0YW1waW5nIEF1dGhvcml0eaCCDykwggeCMIIFaqADAgECAhMz
# AAAABeXPD/9mLsmHAAAAAAAFMA0GCSqGSIb3DQEBDAUAMHcxCzAJBgNVBAYTAlVT
# MR4wHAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xSDBGBgNVBAMTP01pY3Jv
# c29mdCBJZGVudGl0eSBWZXJpZmljYXRpb24gUm9vdCBDZXJ0aWZpY2F0ZSBBdXRo
# b3JpdHkgMjAyMDAeFw0yMDExMTkyMDMyMzFaFw0zNTExMTkyMDQyMzFaMGExCzAJ
# BgNVBAYTAlVTMR4wHAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xMjAwBgNV
# BAMTKU1pY3Jvc29mdCBQdWJsaWMgUlNBIFRpbWVzdGFtcGluZyBDQSAyMDIwMIIC
# IjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAnnznUmP94MWfBX1jtQYioxwe
# 1+eXM9ETBb1lRkd3kcFdcG9/sqtDlwxKoVIcaqDb+omFio5DHC4RBcbyQHjXCwMk
# /l3TOYtgoBjxnG/eViS4sOx8y4gSq8Zg49REAf5huXhIkQRKe3Qxs8Sgp02KHAzn
# Ea/Ssah8nWo5hJM1xznkRsFPu6rfDHeZeG1Wa1wISvlkpOQooTULFm809Z0ZYlQ8
# Lp7i5F9YciFlyAKwn6yjN/kR4fkquUWfGmMopNq/B8U/pdoZkZZQbxNlqJOiBGgC
# Wpx69uKqKhTPVi3gVErnc/qi+dR8A2MiAz0kN0nh7SqINGbmw5OIRC0EsZ31WF3U
# xp3GgZwetEKxLms73KG/Z+MkeuaVDQQheangOEMGJ4pQZH55ngI0Tdy1bi69INBV
# 5Kn2HVJo9XxRYR/JPGAaM6xGl57Ei95HUw9NV/uC3yFjrhc087qLJQawSC3xzY/E
# XzsT4I7sDbxOmM2rl4uKK6eEpurRduOQ2hTkmG1hSuWYBunFGNv21Kt4N20AKmbe
# uSnGnsBCd2cjRKG79+TX+sTehawOoxfeOO/jR7wo3liwkGdzPJYHgnJ54UxbckF9
# 14AqHOiEV7xTnD1a69w/UTxwjEugpIPMIIE67SFZ2PMo27xjlLAHWW3l1CEAFjLN
# Hd3EQ79PUr8FUXetXr0CAwEAAaOCAhswggIXMA4GA1UdDwEB/wQEAwIBhjAQBgkr
# BgEEAYI3FQEEAwIBADAdBgNVHQ4EFgQUa2koOjUvSGNAz3vYr0npPtk92yEwVAYD
# VR0gBE0wSzBJBgRVHSAAMEEwPwYIKwYBBQUHAgEWM2h0dHA6Ly93d3cubWljcm9z
# b2Z0LmNvbS9wa2lvcHMvRG9jcy9SZXBvc2l0b3J5Lmh0bTATBgNVHSUEDDAKBggr
# BgEFBQcDCDAZBgkrBgEEAYI3FAIEDB4KAFMAdQBiAEMAQTAPBgNVHRMBAf8EBTAD
# AQH/MB8GA1UdIwQYMBaAFMh+0mqFKhvKGZgEByfPUBBPaKiiMIGEBgNVHR8EfTB7
# MHmgd6B1hnNodHRwOi8vd3d3Lm1pY3Jvc29mdC5jb20vcGtpb3BzL2NybC9NaWNy
# b3NvZnQlMjBJZGVudGl0eSUyMFZlcmlmaWNhdGlvbiUyMFJvb3QlMjBDZXJ0aWZp
# Y2F0ZSUyMEF1dGhvcml0eSUyMDIwMjAuY3JsMIGUBggrBgEFBQcBAQSBhzCBhDCB
# gQYIKwYBBQUHMAKGdWh0dHA6Ly93d3cubWljcm9zb2Z0LmNvbS9wa2lvcHMvY2Vy
# dHMvTWljcm9zb2Z0JTIwSWRlbnRpdHklMjBWZXJpZmljYXRpb24lMjBSb290JTIw
# Q2VydGlmaWNhdGUlMjBBdXRob3JpdHklMjAyMDIwLmNydDANBgkqhkiG9w0BAQwF
# AAOCAgEAX4h2x35ttVoVdedMeGj6TuHYRJklFaW4sTQ5r+k77iB79cSLNe+GzRjv
# 4pVjJviceW6AF6ycWoEYR0LYhaa0ozJLU5Yi+LCmcrdovkl53DNt4EXs87KDogYb
# 9eGEndSpZ5ZM74LNvVzY0/nPISHz0Xva71QjD4h+8z2XMOZzY7YQ0Psw+etyNZ1C
# esufU211rLslLKsO8F2aBs2cIo1k+aHOhrw9xw6JCWONNboZ497mwYW5EfN0W3zL
# 5s3ad4Xtm7yFM7Ujrhc0aqy3xL7D5FR2J7x9cLWMq7eb0oYioXhqV2tgFqbKHeDi
# ck+P8tHYIFovIP7YG4ZkJWag1H91KlELGWi3SLv10o4KGag42pswjybTi4toQcC/
# irAodDW8HNtX+cbz0sMptFJK+KObAnDFHEsukxD+7jFfEV9Hh/+CSxKRsmnuiovC
# WIOb+H7DRon9TlxydiFhvu88o0w35JkNbJxTk4MhF/KgaXn0GxdH8elEa2Imq45g
# aa8D+mTm8LWVydt4ytxYP/bqjN49D9NZ81coE6aQWm88TwIf4R4YZbOpMKN0Cyej
# aPNN41LGXHeCUMYmBx3PkP8ADHD1J2Cr/6tjuOOCztfp+o9Nc+ZoIAkpUcA/X2gS
# MkgHAPUvIdtoSAHEUKiBhI6JQivRepyvWcl+JYbYbBh7pmgAXVswggefMIIFh6AD
# AgECAhMzAAAAU1LCA4vlmvhOAAAAAABTMA0GCSqGSIb3DQEBDAUAMGExCzAJBgNV
# BAYTAlVTMR4wHAYDVQQKExVNaWNyb3NvZnQgQ29ycG9yYXRpb24xMjAwBgNVBAMT
# KU1pY3Jvc29mdCBQdWJsaWMgUlNBIFRpbWVzdGFtcGluZyBDQSAyMDIwMB4XDTI1
# MDIyNzE5NDAyNloXDTI2MDIyNjE5NDAyNlowgeMxCzAJBgNVBAYTAlVTMRMwEQYD
# VQQIEwpXYXNoaW5ndG9uMRAwDgYDVQQHEwdSZWRtb25kMR4wHAYDVQQKExVNaWNy
# b3NvZnQgQ29ycG9yYXRpb24xLTArBgNVBAsTJE1pY3Jvc29mdCBJcmVsYW5kIE9w
# ZXJhdGlvbnMgTGltaXRlZDEnMCUGA1UECxMeblNoaWVsZCBUU1MgRVNOOjdBMUEt
# MDVFMC1EOTQ3MTUwMwYDVQQDEyxNaWNyb3NvZnQgUHVibGljIFJTQSBUaW1lIFN0
# YW1waW5nIEF1dGhvcml0eTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIB
# AJc5Kfov8wrtUOd6TMY2zReqocHRzPEgqmdkAjU/7fFjMod6kZxF2D068zAvNzvc
# X+nInP7jN3FK2K9R6dp23eNPYXDO/Sxidfo3dKx9YOJu4BmLmB0cSiJxe1OhnFuC
# Yf5cwswZZtA2NrHrr0/xScFReD9VuzjNVftfEGvBbwdpcW4frOYiRwU0aMxGNKfQ
# NET5Nu4KMIjANTjXqARzxXnZPh/wdUXbwRCI8RGUdF7eTUNzL/9rPmzfPSJre3rQ
# +QzB9T2yZLH6tf9cSOkJboq+KUgS8tXojhCTldxp90gYg8FPNhgqDkBA2j29peGp
# qQhZhbMPoHvjVo2LwyLwj515rxO/WxPa2bKLCxjIIHZGEomkOURdxwUU9Wpc7WWC
# hFhiylnc+LSi2eLw5k3ttXQ5taDXaqOaoRDYAZ+4xq/m8qKv8eYsTRLyKMkGwQi+
# Vqw0u6DqD+O9QuVqQI0qhtcECyIxP9dYMcKFedmi7KHGJIouwm6/uatwnbE7lN24
# EaQzqV1OreDyP1tEDKhJerg/sQlRKNDVcmTRIUZVTVomMlZQA9NG+LJke4hgFst9
# eHf0ex/eWg08MitclMvr4Ii2Qe1Z2usrnE4G7oq9rUjZH6Swz9b7qFX9wvVFPEBN
# 8SpwX9sKcf40bDEzivAPgeytqTmSMiNh1QPiMpQh3s5BAgMBAAGjggHLMIIBxzAd
# BgNVHQ4EFgQUbmREqyNjGh8Fs0I9Idb0ZP/2j2owHwYDVR0jBBgwFoAUa2koOjUv
# SGNAz3vYr0npPtk92yEwbAYDVR0fBGUwYzBhoF+gXYZbaHR0cDovL3d3dy5taWNy
# b3NvZnQuY29tL3BraW9wcy9jcmwvTWljcm9zb2Z0JTIwUHVibGljJTIwUlNBJTIw
# VGltZXN0YW1waW5nJTIwQ0ElMjAyMDIwLmNybDB5BggrBgEFBQcBAQRtMGswaQYI
# KwYBBQUHMAKGXWh0dHA6Ly93d3cubWljcm9zb2Z0LmNvbS9wa2lvcHMvY2VydHMv
# TWljcm9zb2Z0JTIwUHVibGljJTIwUlNBJTIwVGltZXN0YW1waW5nJTIwQ0ElMjAy
# MDIwLmNydDAMBgNVHRMBAf8EAjAAMBYGA1UdJQEB/wQMMAoGCCsGAQUFBwMIMA4G
# A1UdDwEB/wQEAwIHgDBmBgNVHSAEXzBdMFEGDCsGAQQBgjdMg30BATBBMD8GCCsG
# AQUFBwIBFjNodHRwOi8vd3d3Lm1pY3Jvc29mdC5jb20vcGtpb3BzL0RvY3MvUmVw
# b3NpdG9yeS5odG0wCAYGZ4EMAQQCMA0GCSqGSIb3DQEBDAUAA4ICAQCIc/9lTzJS
# 0hp0xJqffakNxhlJ8YW6wDGz39WK9mz6Musd5cad4t2Ejje17TAKJmwQwOEgLMT8
# fGNhvCIveXObms4sDuG0CwG5RibIdftJWYc6AEMcziOTD6bKtxd7fvAh4eiVGpPL
# tzCbHFT2DSv5D0ACdPx3XZPjfwFRKAViIyMtL/2bbZjrXu5WLMhXT5ri++Bbi5EO
# 2ygegFkAB+ARoDg0rG5PduDV6dYmVNoHVdAMmXC2KHyrIrHw1J2bPGwC7cFIBz1h
# blfpYub521FApmdHmuU85+0J+Vx4ylXg8y0/pwQcehjD0VGhE3yFgvPDlwMeY4jF
# eI57NihxYzMOPdVJHIo971O+TOsbaojXme3vEdJ56apdvizcq75mAlYz9MpvkJUG
# bMryyijoj9/UGysSu2PJeZcRicMRdjdgphILWGVWqQSo9DinlxgxL+JAP3SRgTpU
# jigrnCB515QwRSDsDFTK0Raoa2uCQSsPmCUyLHOBWrkoCXOPrXJGjuuKpIx1VitZ
# y6/cV5laGGsvuY6jrutyOuGmhdUeLkwpVubgpoLGEJ+c+MtrgIDSpgZuFIBimNQ9
# 8bACqziLHyEaHUTSJjjBbqDX0Y1aciM6v09asFsWq72gRVyFZw2De12wKFxi8MnX
# +4pNOmgkCwXILcwv80Od446mvi1BOajojTGCA9QwggPQAgEBMHgwYTELMAkGA1UE
# BhMCVVMxHjAcBgNVBAoTFU1pY3Jvc29mdCBDb3Jwb3JhdGlvbjEyMDAGA1UEAxMp
# TWljcm9zb2Z0IFB1YmxpYyBSU0EgVGltZXN0YW1waW5nIENBIDIwMjACEzMAAABT
# UsIDi+Wa+E4AAAAAAFMwDQYJYIZIAWUDBAIBBQCgggEtMBoGCSqGSIb3DQEJAzEN
# BgsqhkiG9w0BCRABBDAvBgkqhkiG9w0BCQQxIgQg+6oPjqHuolgnw5J08jo4UQu3
# qbdd9x2+nI+z3+q1Qacwgd0GCyqGSIb3DQEJEAIvMYHNMIHKMIHHMIGgBCBAfx8E
# YoyrlP74wFOwXRwaf7R0X60TD5DXo5XRn9odIzB8MGWkYzBhMQswCQYDVQQGEwJV
# UzEeMBwGA1UEChMVTWljcm9zb2Z0IENvcnBvcmF0aW9uMTIwMAYDVQQDEylNaWNy
# b3NvZnQgUHVibGljIFJTQSBUaW1lc3RhbXBpbmcgQ0EgMjAyMAITMwAAAFNSwgOL
# 5Zr4TgAAAAAAUzAiBCBAGGIF5EEkUqvcCeeSbUwumpbHjLWMDoSce7dTXyhLMjAN
# BgkqhkiG9w0BAQsFAASCAgAf8K6Ck+w50tOt5yJYxKSl95FWqvmycxf53KlKVF/W
# MFxECffN5FhKyBwnQIuLY6ckV6UCKo5STjBMnit1+cFcTVZxzr7Qomla7lLt+dXN
# 3xLHhdBBCfoJqRrW2WgU2zjDgfEOkKSjNB0s1//t7DLoEkZb12XIpqHijIocnfM9
# JwCMkoVFVwRW//30cHkN9Izeox8N7WcEMN/4VJ/Jp9tb/uzoU/LYFIdryXpUZiY8
# kEcFINUjvUMeuCPxYIqW5qxgOdV+pFUM+HMslGpg0Hbl29g/IgydTMU9EdzW6YUb
# PQDXkb/9sId0url7vVMoBq3cXUgGSdz4g5xiGuXLMh5y+7sLVa6X5voeRgOrmg/9
# Wy9JuznvK2Q1eSE0mEhXcD4SAezI6JWqUEBbZXqjA10+37si+oG0x7tihvHcSFvL
# sPsgOMs/PUApOSDbNgCG7r8u4zlC0/M9HZW1MIwDh690Cae+oIqLGSLyy32Jl1iB
# ELeU36RSLmkGx+AOqU3YuI3Bdrw9ZKC0iVM1za7Nmp3W6DTLWGHgUT1+XwOcXcl3
# 4WQvpTLw+whLFWw8HdHwpZ+x1u47GLjgSImenaPClxcNklHu2ZOD+L/Bo0ztAnUc
# izC+faWmg+1WWgXuG76KxG16ogoqtsLijR//4BAJ5wgKyJUtRu2TAqVIY+DKJ5V7
# vA==
# SIG # End signature block
