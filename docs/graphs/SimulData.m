/*  */%% Data
close all
SampleSize = 50;

EnergyTol = 5; % + - 2
ForceTol = 220; % + - 30
HingeTol = 1.7; % + - 0.2

for i=1:SampleSize
    factor = (rand() + rand());
    Energy(i) = 3.5 + factor * 1.5 + rand() * 1;
    Force(i) = 190 + factor * 20 + rand() * 5;
    Spring(i) = Force(i) / 2 + factor * 10 + rand() * 3;
    FO_Energy(i) = 14 + factor * 2 + rand() * 1;
    FO_Speed(i) = FO_Energy(i) * 50 + factor * 100 + rand() * 50;
    CO_Energy(i) = FO_Energy(i) * 0.5 + factor * 4 + rand() * 2;
    CO_Speed(i) = FO_Speed(i) * 0.5 + factor * 100 + rand() * 50;
    Hinge(i) = 1.5 + factor * 0.2 + rand() * 0.1;
    Friction(i) = Hinge(i) * 100 + factor * 200 + rand() * 20;
end

%
Avg_Force=mean(Force);
Std_Force =std(Force);
Avg_FO_Energy=mean(FO_Energy);
Std_FO_Energy =std(FO_Energy);
Avg_FO_Speed=mean(FO_Speed);
Std_FO_Speed =std(FO_Speed);
Avg_Friction=mean(Friction);
Std_Friction =std(Friction);
Avg_CO_Energy=mean(CO_Energy);
Std_CO_Energy =std(CO_Energy);
Avg_CO_Speed=mean(CO_Speed);
Std_CO_Speed =std(CO_Speed);
Avg_Spring=mean(Spring);
Std_Spring =std(Spring);

% Lone Fits
[a_FO_Energy_Speed,b_FO_Energy_Speed]=EZ_F_Linefit(FO_Energy,FO_Speed,0);
[a_Hinge_Friction,b_Hinge_Friction]=EZ_F_Linefit(Hinge,Friction,0);
[a_CO_Energy_Speed,b_CO_Energy_Speed]=EZ_F_Linefit(CO_Energy,CO_Speed,0);
[a_Force_Spring,b_Force_Spring]=EZ_F_Linefit(Force,Spring,0);
[a_Force_Speed,b_Force_Speed]=EZ_F_Linefit(Force,FO_Speed,0);

% Anomalies Up
for i=[18,38,45]
    factor = 0.5 + rand();
    Energy(i) = Energy(i) + factor * 3 + rand() * 1;
    Force(i) = Force(i) + factor * 50  + rand() * 10;
    FO_Energy(i) = FO_Energy(i) + factor * 2  + rand() * 1;
    FO_Speed(i) = CO_Speed(i) + factor * 700  + rand() * 100;
    CO_Energy(i) = FO_Energy(i) + factor * 2  + rand() * 1;
    CO_Speed(i) = CO_Speed(i) + factor * 400  + rand() * 100;
    Hinge(i) =  Hinge(i) + factor * 0.4  + rand() * 0.1;
    Friction(i) =  Friction(i) - factor * 200  + rand() * 20;
end
% Anomalies Down
for i=[22,40]
    factor = 0.5 + rand();
    Energy(i) = Energy(i) - factor * 2 - rand();
    Force(i) = Force(i) - factor * 30 - rand() * 10;
    FO_Energy(i) = FO_Energy(i) - factor * 1 - rand();
    FO_Speed(i) = FO_Speed(i) - factor * 200 - rand() * 20;
    CO_Energy(i) = FO_Energy(i) - factor * 2  - rand() * 1;
    CO_Speed(i) = CO_Speed(i) - factor * 400  - rand() * 100;
    Hinge(i) =  Hinge(i) - factor * 0.4 - rand() * 0.1;
    Friction(i) =  Friction(i) - factor * 200 - rand() * 10;
end


% =========================================================================
% 1.X Sample
% 1.X Closing Energy - First Position
% 1.N Toleranced
% =========================================================================
figure
plot(Energy,'.b','MarkerSize',15)
hold on
reds = find((Energy > EnergyTol+2) | (Energy < EnergyTol-2));
plot(reds,Energy(reds),'.r','MarkerSize',15);

% plot([1,SampleSize],[180,180],'r-')
plot([1,SampleSize],[EnergyTol+2,EnergyTol+2],'r-')

plot([1,SampleSize],[EnergyTol,EnergyTol],'g-')
plot([1,SampleSize],[EnergyTol-2,EnergyTol-2],'r-')

% plot([1,SampleSize],[280,280],'r--')
title('Customer closing Energy from 1st Stop (Toleranced)')
ylabel('Minmimum Closing Energy (J)')
axis([0, 55,0,max(Energy)*1.2])
gz

% =========================================================================
% 2.X Samples
% 2.Y Closing Energy from Full Open
% 2.N Sampled
% =========================================================================
figure
plot(FO_Energy,'.b','MarkerSize',15)
hold on
reds = find((FO_Energy>Avg_FO_Energy+2*Std_FO_Energy) | (FO_Energy<Avg_FO_Energy-2*Std_FO_Energy));
plot(reds,FO_Energy(reds),'.r','MarkerSize',15);

plot([1,SampleSize],[Avg_FO_Energy,Avg_FO_Energy],'k-')
plot([1,SampleSize],[Avg_FO_Energy+2*Std_FO_Energy,Avg_FO_Energy+2*Std_FO_Energy],'k--')
plot([1,SampleSize],[Avg_FO_Energy-2*Std_FO_Energy,Avg_FO_Energy-2*Std_FO_Energy],'k--')

title('Customer closing Energy from Full Open')
ylabel('Minmimum Closing Energy (J)')
axis([0, 55,0,max(FO_Energy)*1.2])
gz

% =========================================================================
% 3.X Energy
% 3.Y Speed
% 3.N Sampled
% =========================================================================
figure
plot(FO_Energy,FO_Speed,'.b','MarkerSize',15)
hold on

reds=[];
for i=1:SampleSize
    TolUp(i) = a_FO_Energy_Speed*FO_Energy(i) + b_FO_Energy_Speed + 2*Std_FO_Speed;
    TolDwn(i) = a_FO_Energy_Speed*FO_Energy(i) + b_FO_Energy_Speed - 2*Std_FO_Speed;
    if (FO_Speed(i) > TolUp(i)) | (FO_Speed(i) < TolDwn(i))
        if isempty(reds)
            reds = i;
        else
            reds(end+1)=i;
        end
    end
end
plot(FO_Energy(reds),FO_Speed(reds),'.r','MarkerSize',15)

minx = min(FO_Energy);
maxx = max(FO_Energy);
plot([minx,maxx],[a_FO_Energy_Speed*minx+b_FO_Energy_Speed,a_FO_Energy_Speed*maxx+b_FO_Energy_Speed],'k-')
plot([minx,maxx],[a_FO_Energy_Speed*minx+b_FO_Energy_Speed+2*Std_FO_Speed,a_FO_Energy_Speed*maxx+b_FO_Energy_Speed+2*Std_FO_Speed],'k--')
plot([minx,maxx],[a_FO_Energy_Speed*minx+b_FO_Energy_Speed-2*Std_FO_Speed,a_FO_Energy_Speed*maxx+b_FO_Energy_Speed-2*Std_FO_Speed],'k--')


title('Hinge and Doorcheck Performance (Sampled)')
xlabel('Minmimum Closing Energy (J)')
ylabel('Minmimum Closing Speed (mm/s)')
axis([min(FO_Energy) * 0.8, max(FO_Energy) *1.2,min(FO_Speed)* 0.8,max(FO_Speed)*1.2])
gz

% =========================================================================
% 4.X Sample
% 4.Y Hinge Tip
% 4.N Tolerance
% =========================================================================
figure
plot(Hinge,'.b','MarkerSize',15)
hold on
reds=find((Hinge>HingeTol+0.3)|(Hinge<HingeTol-0.3));
plot(reds,Hinge(reds),'.r','MarkerSize',15)

plot([1,SampleSize],[HingeTol+0.3,HingeTol+0.3],'r-')
plot([1,SampleSize],[HingeTol,HingeTol],'g-')
plot([1,SampleSize],[HingeTol-0.3,HingeTol-0.3],'r-')
title('Hinge Inclination (Toleranced)')
ylabel('Hinge Angle (deg)')
axis([0, 55,0,max(Hinge)*1.2])
gz

% =========================================================================
% 5.X Hinge tip
% 5.Y Friction Ratio
% 5.N Sampled
% =========================================================================
figure
plot(Hinge,Friction,'.b','MarkerSize',15)
hold on

reds=[];
for i=1:SampleSize
    TolUp(i) = a_Hinge_Friction*Hinge(i) + b_Hinge_Friction + 2*Std_Friction;
    TolDwn(i) = a_Hinge_Friction*Hinge(i) + b_Hinge_Friction - 2*Std_Friction;
    
    if (Friction(i) > TolUp(i))|(Friction(i) < TolDwn(i))
        if isempty(reds)
            reds = i;
        else
            reds(end+1)=i;
        end
    end
end
plot(Hinge(reds),Friction(reds),'.r','MarkerSize',15)

minx = min(Hinge);
maxx = max(Hinge);
plot([minx,maxx],[a_Hinge_Friction*minx+b_Hinge_Friction,a_Hinge_Friction*maxx+b_Hinge_Friction],'k-')
plot([minx,maxx],[a_Hinge_Friction*minx+b_Hinge_Friction+2*Std_Friction,a_Hinge_Friction*maxx+b_Hinge_Friction+2*Std_Friction],'k--')
plot([minx,maxx],[a_Hinge_Friction*minx+b_Hinge_Friction-2*Std_Friction,a_Hinge_Friction*maxx+b_Hinge_Friction-2*Std_Friction],'k--')


title('Hinge Bind (Sampled)')
ylabel('Speed Increase as Kinetic Energy(mm/s)')
% axis([min(Hinge) * 0.8, max(Hinge) *1.2,min(Friction)* 0.8,max(Friction)*1.2])
gz

% =========================================================================
% 6.X Energy - Cabin Vented
% 6.Y Speed
% 6.N Sampled
% =========================================================================
figure
plot(CO_Energy,CO_Speed,'.b','MarkerSize',15)
hold on

reds=[];
for i=1:SampleSize
    TolUp(i) = a_CO_Energy_Speed*CO_Energy(i) + b_CO_Energy_Speed + 2*Std_CO_Speed;
    TolDwn(i) = a_CO_Energy_Speed*CO_Energy(i) + b_CO_Energy_Speed - 2*Std_CO_Speed;
    if (CO_Speed(i) > TolUp(i)) | (CO_Speed(i) < TolDwn(i))
        if isempty(reds)
            reds = i;
        else
            reds(end+1)=i;
        end
    end
end
plot(CO_Energy(reds),CO_Speed(reds),'.r','MarkerSize',15)

minx = min(CO_Energy);
maxx = max(CO_Energy);
plot([minx,maxx],[a_CO_Energy_Speed*minx+b_CO_Energy_Speed,a_CO_Energy_Speed*maxx+b_CO_Energy_Speed],'k-')
plot([minx,maxx],[a_CO_Energy_Speed*minx+b_CO_Energy_Speed+2*Std_CO_Speed,a_CO_Energy_Speed*maxx+b_CO_Energy_Speed+2*Std_CO_Speed],'k--')
plot([minx,maxx],[a_CO_Energy_Speed*minx+b_CO_Energy_Speed-2*Std_CO_Speed,a_CO_Energy_Speed*maxx+b_CO_Energy_Speed-2*Std_CO_Speed],'k--')

title('Door Check Performance, No Cabin (Sampled)')
xlabel('Minmimum Closing Energy (J)')
ylabel('Minmimum Closing Speed (mm/s)')
% axis([0, max(CO_Energy) *1.2,0,max(CO_Speed)*1.2])
gz

% =========================================================================
% 7.X Sample
% 7.Y Force
% 7.N Toleranced
% =========================================================================
figure
plot(Force,'.b','MarkerSize',15)
hold on
reds=find((Force>ForceTol+30)|(Force<ForceTol-30))
plot(reds,Force(reds),'.r','MarkerSize',15)

plot([1,SampleSize],[ForceTol+30,ForceTol+30],'r-')
plot([1,SampleSize],[ForceTol,ForceTol],'g-')
plot([1,SampleSize],[ForceTol-30,ForceTol-30],'r-')
title('Static Closing Force (Toleranced)')
ylabel('Static Force (N)')
axis([0, 55,100,300])
gz

% =========================================================================
% 8.X Force
% 8.Y Spring
% 8.N Sampled
% =========================================================================
figure
plot(Force,Spring,'.b','MarkerSize',15)
hold on

[a,b]=EZ_F_Linefit(Force,Spring,0);
reds=[];
for i=1:SampleSize
    TolUp(i) = a_Force_Spring*Force(i) + b_Force_Spring + 2*Std_Spring;
    TolDwn(i) = a_Force_Spring*Force(i) + b_Force_Spring - 2*Std_Spring;
    if (Spring(i) > TolUp(i))|(Spring(i) < TolDwn(i))
        if isempty(reds)
            reds = i;
        else
            reds(end+1)=i;
        end
    end
end
plot(Force(reds),Spring(reds),'.r','MarkerSize',15)

minx = min(Force);
maxx = max(Force);
plot([minx,maxx],[a_Force_Spring*minx+b_Force_Spring,a_Force_Spring*maxx+b_Force_Spring],'k-')
plot([minx,maxx],[a_Force_Spring*minx+b_Force_Spring+2*Std_Spring,a_Force_Spring*maxx+b_Force_Spring+2*Std_Spring],'k--')
plot([minx,maxx],[a_Force_Spring*minx+b_Force_Spring-2*Std_Spring,a_Force_Spring*maxx+b_Force_Spring-2*Std_Spring],'k--')

title('Striker Alignment (Sampled)')
xlabel('Closing Force (N)')
ylabel('Spring Speed (mm/s)')
% axis([min(Force) * 0.8, max(Force) *1.2,min(Spring)* 0.8,max(Spring)*1.2])
gz

% =========================================================================
% 9. Force
% 9. Speed
% 9.N Sampled
% =========================================================================
figure
plot(Force,FO_Speed,'.b','MarkerSize',15)
hold on

reds=[];
for i=1:SampleSize
    TolUp(i) = a_Force_Speed*Force(i) + b_Force_Speed + 2*Std_FO_Speed;
    TolDwn(i) = a_Force_Speed*Force(i) + b_Force_Speed - 2*Std_FO_Speed;
    
    if (FO_Speed(i) > TolUp(i))|(FO_Speed(i) < TolDwn(i))
        
        if isempty(reds)
            reds = i;
        else
            reds(end+1)=i;
        end
    end
end
plot(Force(reds),FO_Speed(reds),'.r','MarkerSize',15)

minx = min(Force);
maxx = max(Force);
plot([minx,maxx],[a_Force_Speed*minx+b_Force_Speed,a_Force_Speed*maxx+b_Force_Speed],'k-')
plot([minx,maxx],[a_Force_Speed*minx+b_Force_Speed+2*Std_FO_Speed,a_Force_Speed*maxx+b_Force_Speed+2*Std_FO_Speed],'k--')
plot([minx,maxx],[a_Force_Speed*minx+b_Force_Speed-2*Std_FO_Speed,a_Force_Speed*maxx+b_Force_Speed-2*Std_FO_Speed],'k--')


title('Seal Dynamics (Sampled)')
xlabel('Closing Force (N)')
ylabel('Closing Speed (mm/s)')
% axis([0, 50,100,300])
gz








