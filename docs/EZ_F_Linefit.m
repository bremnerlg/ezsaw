function [a,b]=EZ_F_Linefit(X,Y,Origin)

% function [a,b]=EZ_F_Linefit(A,B)
%
% fits a bestfit line from set of (X,Y) points and results in line y=ax+b
% Origin = 0 : points only
% Origin = 1 : points + origin + symmertry

%##########################################################################################
%m number of pairs
[~,n]=size(X);

% Take transpose if only colomn
if n==1
    X=X';
    Y=Y';
    [~,n]=size(X);
end

if Origin==1
    %     X=[X,zeros(1,n)];
    %     Y=[Y,zeros(1,n)];
    X=[X,zeros(1,n),-X];
    Y=[Y,zeros(1,n),-Y];
end


[~,n]=size(X);

sumxy=0;
sumx=0;
sumy=0;
sumx2=0;

for i=1:n
    sumxy=sumxy+X(i)*Y(i);
    sumx=sumx+X(i);
    sumy=sumy+Y(i);
    sumx2=sumx2+X(i)^2;
end

if (n*sumx2-sumx^2)~=0
    a=(n*sumxy-(sumx*sumy))/(n*sumx2-sumx^2);
else
    a=0;
end
b=(sumy-(a*sumx))/n;
%##########################################################################################