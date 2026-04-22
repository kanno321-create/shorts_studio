import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(1);  // 로컬 1080p 9:16, CPU 저사양 안정성 우선
